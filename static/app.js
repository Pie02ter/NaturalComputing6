const state = {
  config: null,
  result: null,
  gaResult: null,
  frameIndex: 0,
  playbackHandle: null,
};

const canvas = document.getElementById("sim-canvas");
const ctx = canvas.getContext("2d");
const gaCanvas = document.getElementById("ga-progress-canvas");
const gaCtx = gaCanvas.getContext("2d");
const comparisonCanvas = document.getElementById("comparison-canvas");
const comparisonCtx = comparisonCanvas.getContext("2d");
const defaultCanvas = document.getElementById("default-canvas");
const defaultCtx = defaultCanvas.getContext("2d");
const gaBestCanvas = document.getElementById("ga-best-canvas");
const gaBestCtx = gaBestCanvas.getContext("2d");

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
  runGaButton: document.getElementById("run-ga-button"),
  runCompareButton: document.getElementById("run-compare-button"),
  playGenerationButton: document.getElementById("play-generation-button"),
  status: document.getElementById("status"),
  ga: {
    populationSize: document.getElementById("ga-population-size"),
    generations: document.getElementById("ga-generations"),
    eliteCount: document.getElementById("ga-elite-count"),
    tournamentSize: document.getElementById("ga-tournament-size"),
    crossoverProbability: document.getElementById("ga-crossover-probability"),
    mutationProbability: document.getElementById("ga-mutation-probability"),
    mutationSigmaScale: document.getElementById("ga-mutation-sigma-scale"),
    rngSeed: document.getElementById("ga-rng-seed"),
    evaluationSeeds: document.getElementById("ga-evaluation-seeds"),
    generationIndex: document.getElementById("ga-generation-index"),
    bestFitness: document.getElementById("ga-best-fitness"),
    selectedGeneration: document.getElementById("ga-selected-generation"),
    summary: document.getElementById("ga-summary"),
    historyBody: document.getElementById("ga-history-body"),
  },
  comparisonSummary: document.getElementById("comparison-summary"),
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

  elements.ga.populationSize.value = state.config.ga_defaults.population_size;
  elements.ga.generations.value = state.config.ga_defaults.generations;
  elements.ga.eliteCount.value = state.config.ga_defaults.elite_count;
  elements.ga.tournamentSize.value = state.config.ga_defaults.tournament_size;
  elements.ga.crossoverProbability.value = state.config.ga_defaults.crossover_probability;
  elements.ga.mutationProbability.value = state.config.ga_defaults.mutation_probability;
  elements.ga.mutationSigmaScale.value = state.config.ga_defaults.mutation_sigma_scale;
  elements.ga.evaluationSeeds.value = state.config.default_evaluation_seeds.join(", ");
}

function getParams() {
  return Array.from(elements.params.querySelectorAll("input[type='range']")).map((slider) => Number(slider.value));
}

function drawFrame(frame) {
  drawFrameOnCanvas(ctx, canvas, state.result, frame);
}

function drawFrameOnCanvas(targetCtx, targetCanvas, result, frame) {
  if (!result || !frame) {
    return;
  }

  const roomWidth = result.room_size[0];
  const roomHeight = result.room_size[1];
  const padding = 24;
  const scale = Math.min((targetCanvas.width - padding * 2) / roomWidth, (targetCanvas.height - padding * 2) / roomHeight);

  const offsetX = (targetCanvas.width - roomWidth * scale) / 2;
  const offsetY = (targetCanvas.height - roomHeight * scale) / 2;

  targetCtx.clearRect(0, 0, targetCanvas.width, targetCanvas.height);

  targetCtx.fillStyle = "#f8fafc";
  targetCtx.fillRect(0, 0, targetCanvas.width, targetCanvas.height);

  targetCtx.strokeStyle = "#334155";
  targetCtx.lineWidth = 2;
  targetCtx.strokeRect(offsetX, offsetY, roomWidth * scale, roomHeight * scale);

  const exitX = offsetX + result.exit_pos[0] * scale;
  const exitY = offsetY + (roomHeight - result.exit_pos[1]) * scale;
  const exitRadius = Math.max(4, result.exit_width * scale * 0.5);

  targetCtx.beginPath();
  targetCtx.fillStyle = "#16a34a";
  targetCtx.arc(exitX, exitY, exitRadius, 0, Math.PI * 2);
  targetCtx.fill();

  frame.positions.forEach((position, index) => {
    if (!frame.active[index]) {
      return;
    }

    const x = offsetX + position[0] * scale;
    const y = offsetY + (roomHeight - position[1]) * scale;
    targetCtx.beginPath();
    targetCtx.fillStyle = frame.types[index] === 1 ? "#2563eb" : "#dc2626";
    targetCtx.arc(x, y, 4, 0, Math.PI * 2);
    targetCtx.fill();
  });

  targetCtx.fillStyle = "#0f172a";
  targetCtx.font = "14px Arial";
  targetCtx.fillText(`Tick ${frame.tick}`, 16, 24);
}

function drawGaProgress() {
  gaCtx.clearRect(0, 0, gaCanvas.width, gaCanvas.height);
  gaCtx.fillStyle = "#f8fafc";
  gaCtx.fillRect(0, 0, gaCanvas.width, gaCanvas.height);

  if (!state.gaResult || !state.gaResult.history.length) {
    gaCtx.fillStyle = "#526077";
    gaCtx.font = "14px Arial";
    gaCtx.fillText("GA progress will appear here after a run.", 20, 30);
    return;
  }

  const history = state.gaResult.history;
  const padding = { top: 20, right: 20, bottom: 36, left: 48 };
  const width = gaCanvas.width - padding.left - padding.right;
  const height = gaCanvas.height - padding.top - padding.bottom;
  const fitnessValues = history.map((entry) => entry.best_fitness);
  const minFitness = Math.min(...fitnessValues);
  const maxFitness = Math.max(...fitnessValues);
  const fitnessRange = Math.max(1e-6, maxFitness - minFitness);

  gaCtx.strokeStyle = "#cbd5e1";
  gaCtx.lineWidth = 1;
  gaCtx.beginPath();
  gaCtx.moveTo(padding.left, padding.top + height);
  gaCtx.lineTo(padding.left + width, padding.top + height);
  gaCtx.moveTo(padding.left, padding.top);
  gaCtx.lineTo(padding.left, padding.top + height);
  gaCtx.stroke();

  gaCtx.strokeStyle = "#7c3aed";
  gaCtx.lineWidth = 2;
  gaCtx.beginPath();
  history.forEach((entry, index) => {
    const x = padding.left + (history.length === 1 ? width / 2 : (index / (history.length - 1)) * width);
    const y = padding.top + height - ((entry.best_fitness - minFitness) / fitnessRange) * height;
    if (index === 0) {
      gaCtx.moveTo(x, y);
    } else {
      gaCtx.lineTo(x, y);
    }
  });
  gaCtx.stroke();

  const selectedIndex = Math.max(0, Math.min(history.length - 1, Number(elements.ga.generationIndex.value) || 0));
  const selectedEntry = history[selectedIndex];
  history.forEach((entry, index) => {
    const x = padding.left + (history.length === 1 ? width / 2 : (index / (history.length - 1)) * width);
    const y = padding.top + height - ((entry.best_fitness - minFitness) / fitnessRange) * height;
    gaCtx.beginPath();
    gaCtx.fillStyle = index === selectedIndex ? "#dc2626" : "#2563eb";
    gaCtx.arc(x, y, index === selectedIndex ? 5 : 3.5, 0, Math.PI * 2);
    gaCtx.fill();
  });

  gaCtx.fillStyle = "#0f172a";
  gaCtx.font = "12px Arial";
  gaCtx.fillText(`Gen 0`, padding.left, gaCanvas.height - 12);
  gaCtx.fillText(`Gen ${history.length - 1}`, padding.left + width - 46, gaCanvas.height - 12);
  gaCtx.fillText(`Best ${minFitness.toFixed(2)}`, 10, padding.top + 10);
  gaCtx.fillText(`Worst ${maxFitness.toFixed(2)}`, 10, padding.top + 26);

  elements.ga.selectedGeneration.textContent = `${selectedEntry.generation}`;
}

function drawComparisonChart() {
  comparisonCtx.clearRect(0, 0, comparisonCanvas.width, comparisonCanvas.height);
  comparisonCtx.fillStyle = "#f8fafc";
  comparisonCtx.fillRect(0, 0, comparisonCanvas.width, comparisonCanvas.height);

  if (!state.gaResult || !state.gaResult.comparisonMethods || !state.gaResult.comparisonMethods.length) {
    comparisonCtx.fillStyle = "#526077";
    comparisonCtx.font = "14px Arial";
    comparisonCtx.fillText("Method comparison will appear here after a comparison run.", 20, 30);
    return;
  }

  const methods = state.gaResult.comparisonMethods;
  const padding = { top: 20, right: 20, bottom: 60, left: 50 };
  const width = comparisonCanvas.width - padding.left - padding.right;
  const height = comparisonCanvas.height - padding.top - padding.bottom;
  const maxFitness = Math.max(...methods.map((item) => item.fitness), 1);
  const barWidth = width / methods.length * 0.62;

  comparisonCtx.strokeStyle = "#cbd5e1";
  comparisonCtx.beginPath();
  comparisonCtx.moveTo(padding.left, padding.top + height);
  comparisonCtx.lineTo(padding.left + width, padding.top + height);
  comparisonCtx.moveTo(padding.left, padding.top);
  comparisonCtx.lineTo(padding.left, padding.top + height);
  comparisonCtx.stroke();

  methods.forEach((method, index) => {
    const x = padding.left + (index + 0.2) * (width / methods.length);
    const barHeight = (method.fitness / maxFitness) * height;
    const y = padding.top + height - barHeight;
    comparisonCtx.fillStyle = method.method === "ga" ? "#7c3aed" : method.method === "default" ? "#0f766e" : "#2563eb";
    comparisonCtx.fillRect(x, y, barWidth, barHeight);
    comparisonCtx.fillStyle = "#0f172a";
    comparisonCtx.font = "12px Arial";
    comparisonCtx.save();
    comparisonCtx.translate(x + barWidth / 2, padding.top + height + 16);
    comparisonCtx.rotate(-0.4);
    comparisonCtx.fillText(method.method, -18, 0);
    comparisonCtx.restore();
    comparisonCtx.fillText(method.fitness.toFixed(1), x, y - 6);
  });
}

function populateHistoryTable(history) {
  if (!history || !history.length) {
    elements.ga.historyBody.innerHTML = '<tr><td colspan="3">Run the GA to populate this table.</td></tr>';
    return;
  }

  elements.ga.historyBody.innerHTML = history
    .map((entry) => {
      const params = entry.best_params.map((value) => Number(value).toFixed(2)).join(", ");
      return `<tr><td>${entry.generation}</td><td>${entry.best_fitness.toFixed(3)}</td><td class="param-cell">[${params}]</td></tr>`;
    })
    .join("");
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

function playComparisonFrames(defaultResult, gaResult) {
  if (!defaultResult || !gaResult) {
    return;
  }

  let frameIndex = 0;
  const maxFrames = Math.max(defaultResult.frames.length, gaResult.frames.length);
  let lastTime = 0;

  const render = (timestamp) => {
    if (timestamp - lastTime > 90) {
      const defaultFrame = defaultResult.frames[Math.min(frameIndex, defaultResult.frames.length - 1)];
      const gaFrame = gaResult.frames[Math.min(frameIndex, gaResult.frames.length - 1)];
      drawFrameOnCanvas(defaultCtx, defaultCanvas, defaultResult, defaultFrame);
      drawFrameOnCanvas(gaBestCtx, gaBestCanvas, gaResult, gaFrame);
      frameIndex += 1;
      lastTime = timestamp;
    }

    if (frameIndex < maxFrames) {
      requestAnimationFrame(render);
    }
  };

  requestAnimationFrame(render);
}

function parseEvaluationSeeds() {
  return elements.ga.evaluationSeeds.value
    .split(",")
    .map((value) => value.trim())
    .filter((value) => value.length > 0)
    .map((value) => Number(value));
}

function currentSimulationPayload() {
  return {
    layout: elements.layout.value,
    seed: Number(elements.seed.value),
    num_high: Number(elements.numHigh.value),
    num_low: Number(elements.numLow.value),
    max_ticks: Number(elements.maxTicks.value),
    dt: Number(elements.dt.value),
    params: getParams(),
  };
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
  const payload = currentSimulationPayload();

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

async function replayGenerationChampion() {
  if (!state.gaResult || !state.gaResult.history.length) {
    setStatus("Run the GA first.");
    return;
  }

  const history = state.gaResult.history;
  const generationIndex = Math.max(0, Math.min(history.length - 1, Number(elements.ga.generationIndex.value) || 0));
  const champion = history[generationIndex];
  const payload = currentSimulationPayload();
  payload.params = champion.best_params;

  setStatus(`Replaying generation ${champion.generation} champion...`);
  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Replay request failed.");
    }

    state.result = result;
    updateMetrics(result);
    playFrames();
    drawGaProgress();
    setStatus(`Showing generation ${champion.generation} champion.`);
  } catch (error) {
    setStatus(error.message);
  }
}

async function runGa() {
  const payload = {
    ...currentSimulationPayload(),
    population_size: Number(elements.ga.populationSize.value),
    generations: Number(elements.ga.generations.value),
    elite_count: Number(elements.ga.eliteCount.value),
    tournament_size: Number(elements.ga.tournamentSize.value),
    crossover_probability: Number(elements.ga.crossoverProbability.value),
    mutation_probability: Number(elements.ga.mutationProbability.value),
    mutation_sigma_scale: Number(elements.ga.mutationSigmaScale.value),
    rng_seed: Number(elements.ga.rngSeed.value),
    evaluation_seeds: parseEvaluationSeeds(),
    visualization_seed: Number(elements.seed.value),
  };

  elements.runGaButton.disabled = true;
  setStatus("Running GA optimization...");

  try {
    const response = await fetch("/api/optimize/ga", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "GA request failed.");
    }

    state.gaResult = result;
    state.result = result.best_simulation;
    state.gaResult.comparisonMethods = null;
    elements.ga.generationIndex.max = Math.max(0, result.history.length - 1);
    elements.ga.generationIndex.value = Math.max(0, result.history.length - 1);
    elements.ga.bestFitness.textContent = formatMetric(result.best.fitness);
    elements.ga.summary.textContent = `Best fitness ${formatMetric(result.best.fitness)} after ${result.history.length} generations. Click replay to inspect any generation champion.`;
    updateMetrics(result.best_simulation);
    drawGaProgress();
    drawComparisonChart();
    populateHistoryTable(result.history);
    playFrames();
    setStatus("GA complete. Showing the best evolved simulation.");
  } catch (error) {
    setStatus(error.message);
  } finally {
    elements.runGaButton.disabled = false;
  }
}

async function runComparison() {
  const payload = {
    ...currentSimulationPayload(),
    population_size: Number(elements.ga.populationSize.value),
    generations: Number(elements.ga.generations.value),
    elite_count: Number(elements.ga.eliteCount.value),
    tournament_size: Number(elements.ga.tournamentSize.value),
    crossover_probability: Number(elements.ga.crossoverProbability.value),
    mutation_probability: Number(elements.ga.mutationProbability.value),
    mutation_sigma_scale: Number(elements.ga.mutationSigmaScale.value),
    rng_seed: Number(elements.ga.rngSeed.value),
    evaluation_seeds: parseEvaluationSeeds(),
    visualization_seed: Number(elements.seed.value),
  };

  elements.runCompareButton.disabled = true;
  setStatus("Running method comparison...");

  try {
    const response = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Comparison request failed.");
    }

    state.gaResult = state.gaResult || {};
    state.gaResult.comparisonMethods = result.methods;
    state.gaResult.history = result.ga_history;
    elements.ga.generationIndex.max = Math.max(0, result.ga_history.length - 1);
    elements.ga.generationIndex.value = Math.max(0, result.ga_history.length - 1);
    elements.ga.bestFitness.textContent = formatMetric(result.methods.find((item) => item.method === "ga")?.fitness);
    elements.ga.summary.textContent = "Comparison includes default, two heuristics, random search, and GA under the same scenario.";
    elements.comparisonSummary.textContent = `Compared ${result.methods.length} methods using visualization seed ${result.visualization_seed}.`;
    drawGaProgress();
    drawComparisonChart();
    populateHistoryTable(result.ga_history);
    playComparisonFrames(result.default_simulation, result.ga_best_simulation);
    setStatus("Comparison complete. Showing default versus GA-best side by side.");
  } catch (error) {
    setStatus(error.message);
  } finally {
    elements.runCompareButton.disabled = false;
  }
}

async function init() {
  const response = await fetch("/api/config");
  state.config = await response.json();
  fillControls();
  buildParams();
  drawGaProgress();
  drawComparisonChart();
  populateHistoryTable([]);
  setStatus("Ready.");
}

elements.runButton.addEventListener("click", runSimulation);
elements.replayButton.addEventListener("click", playFrames);
elements.runGaButton.addEventListener("click", runGa);
elements.runCompareButton.addEventListener("click", runComparison);
elements.playGenerationButton.addEventListener("click", replayGenerationChampion);
elements.ga.generationIndex.addEventListener("input", drawGaProgress);

init();
