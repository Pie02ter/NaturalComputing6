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
    fitnessWeights: document.getElementById("fitness-weights"),
    randomCandidates: document.getElementById("random-candidates"),
    randomRngSeed: document.getElementById("random-rng-seed"),
    runCompareButton: document.getElementById("run-compare-button"),
    status: document.getElementById("status"),
    comparisonSummary: document.getElementById("comparison-summary"),
    methodBody: document.getElementById("method-body"),
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
  };
  const comparisonCanvas = document.getElementById("comparison-canvas");
  const comparisonCtx = comparisonCanvas.getContext("2d");
  const progressCanvas = document.getElementById("ga-progress-canvas");
  const progressCtx = progressCanvas.getContext("2d");
  const defaultCanvas = document.getElementById("default-canvas");
  const defaultCtx = defaultCanvas.getContext("2d");
  const gaBestCanvas = document.getElementById("ga-best-canvas");
  const gaBestCtx = gaBestCanvas.getContext("2d");
  const state = { config: null, result: null };

  function payload() {
    const gaSettings = Common.readGaSettings(elements.gaFields);
    return {
      ...Common.readScenarioPayload(elements),
      evaluation_seeds: Common.parseSeedList(elements.evaluationSeeds.value, state.config.default_evaluation_seeds),
      fitness_weights: Common.readFitnessWeights(elements.fitnessWeights),
      random_candidates: Number(elements.randomCandidates.value),
      random_rng_seed: Number(elements.randomRngSeed.value),
      population_size: gaSettings.population_size,
      generations: gaSettings.generations,
      elite_count: gaSettings.elite_count,
      tournament_size: gaSettings.tournament_size,
      crossover_probability: gaSettings.crossover_probability,
      mutation_probability: gaSettings.mutation_probability,
      mutation_sigma_scale: gaSettings.mutation_sigma_scale,
      rng_seed: gaSettings.rng_seed,
      visualization_seed: Number(elements.seed.value),
    };
  }

  function render() {
    const methods = state.result ? state.result.methods : [];
    const history = state.result ? state.result.ga_history : [];
    Common.drawBarChart(comparisonCtx, comparisonCanvas, methods, "Method comparison will appear here after a comparison run.");
    Common.drawLineChart(progressCtx, progressCanvas, history.map((entry) => entry.best_fitness), history.length - 1, "GA convergence appears here after a comparison run.");
    Common.renderMethodSummaryTable(elements.methodBody, methods);
  }

  async function runComparison() {
    elements.runCompareButton.disabled = true;
    Common.setStatus(elements.status, "Running comparison...");
    try {
      const response = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload()),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Comparison request failed.");
      }
      state.result = result;
      render();
      Common.playSynchronizedResults([
        { ctx: defaultCtx, canvas: defaultCanvas, result: result.default_simulation },
        { ctx: gaBestCtx, canvas: gaBestCanvas, result: result.ga_best_simulation },
      ]);
      elements.comparisonSummary.textContent = `Compared ${result.methods.length} methods using ${result.evaluation_seeds.length} evaluation seeds.`;
      Common.setStatus(elements.status, "Comparison complete. Showing default versus GA-best side by side.");
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    } finally {
      elements.runCompareButton.disabled = false;
    }
  }

  elements.runCompareButton.addEventListener("click", runComparison);

  state.config = await Common.fetchConfig();
  Common.fillScenarioControls(elements, state.config);
  Common.buildFitnessWeightControls(elements.fitnessWeights, state.config.default_fitness_weights);
  Common.fillGaControls(elements.gaFields, state.config, { rng_seed: 123 });
  elements.randomCandidates.value = state.config.ga_defaults.population_size * state.config.ga_defaults.generations;
  elements.evaluationSeeds.value = state.config.default_evaluation_seeds.join(", ");
  render();
  Common.setStatus(elements.status, "Ready.");
});
