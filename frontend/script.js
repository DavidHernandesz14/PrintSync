
const jobForm = document.getElementById("job-form");
const jobNameInput = document.getElementById("job-name");
const durationInput = document.getElementById("job-duration");
const submitButton = document.getElementById("submit-button");
const startButton = document.getElementById("start-button");

const formMessage = document.getElementById("form-message");
const schedulerMessage =
    document.getElementById("scheduler-message");

let latestStatus = null;
let requestPending = false;

function setMessage(element, message, isError = false) {
    element.textContent = message;
    element.classList.toggle("error", isError);
}

function formatSeconds(value) {
    return `${Number(value).toFixed(2)}s`;
}

async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || `Request failed: ${response.status}`
        );
    }

    return data;
}

function updateButtons() {
    const running = latestStatus?.scheduler_running ?? false;
    const pending = latestStatus?.pending_jobs.length ?? 0;

    submitButton.disabled = running || requestPending;
    startButton.disabled = running || pending === 0 || requestPending;

    startButton.textContent = running
        ? "Scheduler Running..."
        : "Start SJF Scheduler";
}

function updateStatistics(data) {
    const printers = data.printers;
    const completed = data.completed_jobs;

    const activeCount = printers.filter(
        (printer) => printer.status === "Printing"
    ).length;

    document.getElementById("total-printers").textContent =
        printers.length;

    document.getElementById("active-printers").textContent =
        activeCount;

    document.getElementById("queued-jobs").textContent =
        data.pending_jobs.length;

    document.getElementById("completed-count").textContent =
        completed.length;
}

function renderPrinters(printers) {
    const grid = document.getElementById("printer-grid");
    grid.replaceChildren();

    for (const printer of printers) {
        const card = document.createElement("div");
        card.className = "printer-card";

        const top = document.createElement("div");
        top.className = "printer-top";

        const title = document.createElement("h3");
        title.textContent = printer.name;

        const badge = document.createElement("span");
        badge.className = "status-badge";

        const status = printer.status;
        badge.textContent = status;

        if (status === "Printing") {
            badge.classList.add("status-printing");
        } else if (status === "Completed") {
            badge.classList.add("status-completed");
        } else {
            badge.classList.add("status-idle");
        }

        top.append(title, badge);

        const job = document.createElement("p");
        job.className = "printer-job";
        job.textContent = printer.current_job
            ? `Current Job: ${printer.current_job}`
            : "No active print job";

        const progressHeader = document.createElement("div");
        progressHeader.className = "progress-header";

        const progressLabel = document.createElement("span");
        progressLabel.textContent = "Progress";

        const progressValue = document.createElement("span");
        progressValue.textContent = `${printer.progress}%`;

        progressHeader.append(progressLabel, progressValue);

        const progressBar = document.createElement("div");
        progressBar.className = "progress-bar";

        const progressFill = document.createElement("div");
        progressFill.className = "progress-fill";
        progressFill.style.width =
            `${Math.max(0, Math.min(100, printer.progress))}%`;

        progressBar.appendChild(progressFill);

        card.append(top, job, progressHeader, progressBar);
        grid.appendChild(card);
    }
}

function renderQueue(jobs) {
    const list = document.getElementById("queue-list");
    const count = document.getElementById("queue-count");

    list.replaceChildren();
    count.textContent = `${jobs.length} Jobs`;

    if (jobs.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-message";
        empty.textContent = "No jobs waiting.";
        list.appendChild(empty);
        return;
    }

    for (const [index, job] of jobs.entries()) {
        const item = document.createElement("div");
        item.className = "queue-item";

        const info = document.createElement("div");

        const name = document.createElement("strong");
        name.textContent = `${index + 1}. ${job.job_name}`;

        const duration = document.createElement("span");
        duration.textContent =
            `Estimated: ${formatSeconds(job.duration)}`;

        info.append(name, duration);
        item.appendChild(info);
        list.appendChild(item);
    }
}

function renderCompletedJobs(jobs) {
    const table = document.getElementById("completed-table");
    table.replaceChildren();

    if (jobs.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 5;
        cell.className = "empty-message";
        cell.textContent = "No completed jobs yet.";

        row.appendChild(cell);
        table.appendChild(row);
    }

    for (const job of jobs) {
        const row = document.createElement("tr");

        const values = [
            job.job_name,
            job.printer,
            formatSeconds(job.duration),
            formatSeconds(job.waiting_time),
            formatSeconds(job.turnaround_time),
        ];

        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        }

        table.appendChild(row);
    }

    const totalWaiting = jobs.reduce(
        (sum, job) => sum + job.waiting_time,
        0
    );

    const totalTurnaround = jobs.reduce(
        (sum, job) => sum + job.turnaround_time,
        0
    );

    const averageWait =
        jobs.length > 0 ? totalWaiting / jobs.length : 0;

    const averageTurnaround =
        jobs.length > 0 ? totalTurnaround / jobs.length : 0;

    document.getElementById("average-wait").textContent =
        formatSeconds(averageWait);

    document.getElementById("average-turnaround").textContent =
        formatSeconds(averageTurnaround);
}

async function refreshDashboard() {
    const connection =
        document.getElementById("connection-status");

    try {
        const data = await apiRequest("/status");

        latestStatus = data;

        connection.textContent = "System Online";
        connection.className = "connection online";

        updateStatistics(data);
        renderPrinters(data.printers);
        renderQueue(data.pending_jobs);
        renderCompletedJobs(data.completed_jobs);
        updateButtons();

    } catch (error) {
        connection.textContent = "System Offline";
        connection.className = "connection offline";

        submitButton.disabled = true;
        startButton.disabled = true;

        console.error("Dashboard update failed:", error);
    }
}

jobForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (requestPending) return;

    requestPending = true;
    updateButtons();

    const jobName = jobNameInput.value.trim();
    const duration = Number(durationInput.value);

    if (!jobName || !Number.isFinite(duration) || duration <= 0) {
        setMessage(formMessage, "Enter a valid job.", true);
        requestPending = false;
        updateButtons();
        return;
    }

    try {
        await apiRequest("/jobs", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                job_name: jobName,
                duration: duration,
            }),
        });

        setMessage(formMessage, "Job added to the queue!");

        jobForm.reset();
        jobNameInput.focus();

        await refreshDashboard();

    } catch (error) {
        setMessage(formMessage, error.message, true);
    } finally {
        requestPending = false;
        updateButtons();
    }
});

startButton.addEventListener("click", async () => {
    if (requestPending) return;

    requestPending = true;
    updateButtons();

    try {
        await apiRequest("/scheduler/start", {
            method: "POST",
        });

        setMessage(
            schedulerMessage,
            "SJF scheduler started successfully!"
        );

        await refreshDashboard();

    } catch (error) {
        setMessage(schedulerMessage, error.message, true);
    } finally {
        requestPending = false;
        updateButtons();
    }
});

// Refresh once immediately, then every second.
refreshDashboard();
setInterval(refreshDashboard, 1000);
