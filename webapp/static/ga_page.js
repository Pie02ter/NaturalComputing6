document.addEventListener("DOMContentLoaded", async () => {
  const Common = window.AppCommon;
  const elements = {
    layout: document.getElementById("layout"),
    seed: document.getElementById("seed"),
    numHigh: document.getElementById("num-high"),
    numLow: document.getElementById("num-low"),
    maxTicks: document.getElementById("max-ticks"),
    dt: document.getElementById("dt"),
    evaluationSeeds: document.getElementById("evaluation-seeds"),
    gaParams: document.getElementById("ga-params"),
    fixedWallSummary: document.getElementById("fixed-wall-summary"),
    fitnessWeights: document.getElementById("fitness-weights"),
    status: document.getElementById("status"),
    runGaButton: document.getElementById("run-ga-button"),
    replayGenerationButton: document.getElementById("replay-generation-button"),
    generationIndex: document.getElementById("generation-index"),
    bestFitness: document.getElementById("best-fitness"),
    selectedGeneration: document.getElementById("selected-generation"),
    bestParams: document.getElementById("best-params"),
    gaSummary: document.getElementById("ga-summary"),
    historyBody: document.getElementById("history-body"),
    gaFields: {
      populationSize: document.getElementById("population-size"),
      generations: document.getElementById("generations"),
      eliteCount: document.getElementById("elite-count"),
      tournamentSize: document.getElementById("tournament-size"),
      crossoverProbability: document.getElementById("crossover-probability"),
      mutationProbability: document.getElementById("mutation-probability"),
      mutationSigmaScale: document.getElementById("mutation-sigma-scale"),
      rngSeed: document.getElementById("rng-seed"),
    },
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
  const canvas = document.getElementById("sim-canvas");
  const ctx = canvas.getContext("2d");
  const playback = Common.createPlayback(ctx, canvas);
  const progressCanvas = document.getElementById("ga-progress-canvas");
  const progressCtx = progressCanvas.getContext("2d");
  const state = { config: null, gaResult: null, result: null };

  function currentPayload() {
    return {
      ...Common.readScenarioPayload(elements),
      evaluation_seeds: Common.parseSeedList(elements.evaluationSeeds.value, state.config.default_evaluation_seeds),
      fitness_weights: Common.readFitnessWeights(elements.fitnessWeights),
      ...Common.readGaSettings(elements.gaFields),
      visualization_seed: Number(elements.seed.value),
      ga_seed_vector: Common.readGaParamValues(elements.gaParams),
    };
  }

  function renderGa() {
    const history = state.gaResult ? state.gaResult.history : [];
    const selectedIndex = Math.max(0, Math.min(history.length - 1, Number(elements.generationIndex.value) || 0));
    Common.drawLineChart(progressCtx, progressCanvas, history.map((entry) => entry.best_fitness), selectedIndex, "GA progress will appear here after a run.");
    Common.renderHistoryTable(elements.historyBody, history);
    if (!history.length) {
      elements.selectedGeneration.textContent = "-";
      return;
    }
    elements.selectedGeneration.textContent = `${history[selectedIndex].generation}`;
  }

  async function runGa() {
    elements.runGaButton.disabled = true;
    Common.setStatus(elements.status, "Running GA optimization...");
    try {
      const response = await fetch("/api/optimize/ga", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentPayload()),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "GA request failed.");
      }
      state.gaResult = result;
      state.result = result.best_simulation;
      Common.updateMetrics(elements.metrics, result.best_simulation);
      playback.play(result.best_simulation);
      elements.generationIndex.max = Math.max(0, result.history.length - 1);
      elements.generationIndex.value = Math.max(0, result.history.length - 1);
      elements.bestFitness.textContent = Common.formatMetric(result.best.fitness, 3);
      elements.bestParams.textContent = `[${result.best.params.map((value) => Number(value).toFixed(2)).join(", ")}]`;
      elements.gaSummary.textContent = `Best fitness ${Common.formatMetric(result.best.fitness, 3)} using ${result.evaluation_seeds.length} evaluation seeds.`;
      renderGa();
      Common.setStatus(elements.status, "GA complete. Showing the best evolved simulation.");
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    } finally {
      elements.runGaButton.disabled = false;
    }
  }

  async function replayGeneration() {
    if (!state.gaResult || !state.gaResult.history.length) {
      Common.setStatus(elements.status, "Run the GA first.");
      return;
    }
    const history = state.gaResult.history;
    const selectedIndex = Math.max(0, Math.min(history.length - 1, Number(elements.generationIndex.value) || 0));
    const champion = history[selectedIndex];
    Common.setStatus(elements.status, `Replaying generation ${champion.generation} champion...`);
    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...Common.readScenarioPayload(elements), params: champion.best_params }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Replay request failed.");
      }
      state.result = result;
      Common.updateMetrics(elements.metrics, result);
      playback.play(result);
      renderGa();
      Common.setStatus(elements.status, `Showing generation ${champion.generation} champion.`);
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    }
  }

  elements.runGaButton.addEventListener("click", runGa);
  elements.replayGenerationButton.addEventListener("click", replayGeneration);
  elements.generationIndex.addEventListener("input", renderGa);

  state.config = await Common.fetchConfig();
  Common.fillScenarioControls(elements, state.config);
  Common.buildGaParamControls(elements.gaParams, state.config);
  Common.renderFixedWallSummary(elements.fixedWallSummary, state.config);
  Common.buildFitnessWeightControls(elements.fitnessWeights, state.config.default_fitness_weights);
  Common.fillGaControls(elements.gaFields, state.config, { rng_seed: 123 });
  elements.evaluationSeeds.value = state.config.default_evaluation_seeds.join(", ");
  renderGa();
  Common.setStatus(elements.status, "Ready.");
});
