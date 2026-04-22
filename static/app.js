const state = {
  config: null,
  result: null,
  frameIndex: 0,
  playbackHandle: null,
};

const canvas = document.getElementById("sim-canvas");
const ctx = canvas.getContext("2d");

const elements = {
  layout: document.getElementById("layout"),
  seed: document.getElementById("seed"),
  numHigh: document.getElementById("num-high"),
  numLow: document.getElementById("num-low"),
  maxTicks: document.getElementById("max-ticks"),
  dt: document.getElementById("dt"),
  params: document.getElementById("params"),
  runButton: document.getElementById("run-button"),
  replayButton: document.getElementById("replay-button"),
  status: document.getElementById("status"),
  metrics: {
    ticks: document.getElementById("metric-ticks"),
    time: document.getElementById("metric-time"),
    evacuated: document.getElementById("metric-evacuated"),
    remaining: document.getElementById("metric-remaining"),
    collisions: document.getElementById("metric-collisions"),
    congestion: document.getElementById("metric-congestion"),
    high: document.getElementById("metric-high"),
    low: document.getElementById("metric-low"),
    gap: document.getElementById("metric-gap"),
  },
};

function setStatus(message) {
  elements.status.textContent = message;
}

function formatMetric(value, digits = 2) {
  if (value === null || value === undefined) {
    return "-";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? `${value}` : value.toFixed(digits);
  }

  return `${value}`;
}

function buildParams() {
  elements.params.innerHTML = "";

  state.config.param_names.forEach((name, index) => {
    const [min, max] = state.config.param_bounds[index];
    const value = state.config.default_params[index];
    const row = document.createElement("label");
    row.className = "param-row";

    const header = document.createElement("div");
    header.className = "param-header";
    header.innerHTML = `<span>${name}</span><span id="param-value-${index}">${value.toFixed(2)}</span>`;

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = min;
    slider.max = max;
    slider.step = "0.05";
    slider.value = value;
    slider.dataset.index = index;
    slider.addEventListener("input", (event) => {
      document.getElementById(`param-value-${event.target.dataset.index}`).textContent = Number(event.target.value).toFixed(2);
    });

    row.appendChild(header);
    row.appendChild(slider);
    elements.params.appendChild(row);
  });
}

function fillControls() {
  elements.layout.innerHTML = "";
  Object.keys(state.config.layouts).forEach((layoutName) => {
    const option = document.createElement("option");
    option.value = layoutName;
    option.textContent = layoutName;
    elements.layout.appendChild(option);
  });

  elements.layout.value = state.config.defaults.layout;
  elements.seed.value = state.config.defaults.seed;
  elements.numHigh.value = state.config.defaults.num_high;
  elements.numLow.value = state.config.defaults.num_low;
  elements.maxTicks.value = state.config.defaults.max_ticks;
  elements.dt.value = state.config.defaults.dt;
}

function getParams() {
  return Array.from(elements.params.querySelectorAll("input[type='range']")).map((slider) => Number(slider.value));
}

function drawFrame(frame) {
  if (!state.result || !frame) {
    return;
  }

  const roomWidth = state.result.room_size[0];
  const roomHeight = state.result.room_size[1];
  const padding = 24;
  const scale = Math.min((canvas.width - padding * 2) / roomWidth, (canvas.height - padding * 2) / roomHeight);

  const offsetX = (canvas.width - roomWidth * scale) / 2;
  const offsetY = (canvas.height - roomHeight * scale) / 2;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#f8fafc";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "#334155";
  ctx.lineWidth = 2;
  ctx.strokeRect(offsetX, offsetY, roomWidth * scale, roomHeight * scale);

  const exitX = offsetX + state.result.exit_pos[0] * scale;
  const exitY = offsetY + (roomHeight - state.result.exit_pos[1]) * scale;
  const exitRadius = Math.max(4, state.result.exit_width * scale * 0.5);

  ctx.beginPath();
  ctx.fillStyle = "#16a34a";
  ctx.arc(exitX, exitY, exitRadius, 0, Math.PI * 2);
  ctx.fill();

  frame.positions.forEach((position, index) => {
    if (!frame.active[index]) {
      return;
    }

    const x = offsetX + position[0] * scale;
    const y = offsetY + (roomHeight - position[1]) * scale;
    ctx.beginPath();
    ctx.fillStyle = frame.types[index] === 1 ? "#2563eb" : "#dc2626";
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.fillStyle = "#0f172a";
  ctx.font = "14px Arial";
  ctx.fillText(`Tick ${frame.tick}`, 16, 24);
}

function stopPlayback() {
  if (state.playbackHandle !== null) {
    cancelAnimationFrame(state.playbackHandle);
    state.playbackHandle = null;
  }
}

function playFrames() {
  stopPlayback();

  if (!state.result || !state.result.frames.length) {
    return;
  }

  state.frameIndex = 0;
  let lastTime = 0;

  const render = (timestamp) => {
    if (timestamp - lastTime > 90) {
      drawFrame(state.result.frames[state.frameIndex]);
      state.frameIndex += 1;
      lastTime = timestamp;
    }

    if (state.frameIndex < state.result.frames.length) {
      state.playbackHandle = requestAnimationFrame(render);
    } else {
      state.playbackHandle = null;
    }
  };

  state.playbackHandle = requestAnimationFrame(render);
}

function updateMetrics(result) {
  elements.metrics.ticks.textContent = formatMetric(result.ticks);
  elements.metrics.time.textContent = formatMetric(result.total_time);
  elements.metrics.evacuated.textContent = formatMetric(result.evacuated_agents);
  elements.metrics.remaining.textContent = formatMetric(result.remaining_agents);
  elements.metrics.collisions.textContent = formatMetric(result.near_collisions);
  elements.metrics.congestion.textContent = formatMetric(result.mean_congestion);
  elements.metrics.high.textContent = formatMetric(result.mean_high_time);
  elements.metrics.low.textContent = formatMetric(result.mean_low_time);
  elements.metrics.gap.textContent = formatMetric(result.fairness_gap_time);
}

async function runSimulation() {
  const payload = {
    layout: elements.layout.value,
    seed: Number(elements.seed.value),
    num_high: Number(elements.numHigh.value),
    num_low: Number(elements.numLow.value),
    max_ticks: Number(elements.maxTicks.value),
    dt: Number(elements.dt.value),
    params: getParams(),
  };

  elements.runButton.disabled = true;
  setStatus("Running simulation...");

  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Simulation request failed.");
    }

    state.result = result;
    updateMetrics(result);
    playFrames();
    setStatus(result.all_evacuated ? "Simulation complete." : "Simulation hit max ticks before everyone evacuated.");
  } catch (error) {
    setStatus(error.message);
  } finally {
    elements.runButton.disabled = false;
  }
}

async function init() {
  const response = await fetch("/api/config");
  state.config = await response.json();
  fillControls();
  buildParams();
  setStatus("Ready.");
}

elements.runButton.addEventListener("click", runSimulation);
elements.replayButton.addEventListener("click", playFrames);

init();
