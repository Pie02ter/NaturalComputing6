document.addEventListener("DOMContentLoaded", async () => {
  const Common = window.AppCommon;
  const elements = {
    preset: document.getElementById("preset"),
    suite: document.getElementById("suite"),
    presetDescription: document.getElementById("preset-description"),
    layout: document.getElementById("layout"),
    seed: document.getElementById("seed"),
    numHigh: document.getElementById("num-high"),
    numLow: document.getElementById("num-low"),
    maxTicks: document.getElementById("max-ticks"),
    dt: document.getElementById("dt"),
    evaluationSeeds: document.getElementById("evaluation-seeds"),
    fitnessWeights: document.getElementById("fitness-weights"),
    randomCandidates: document.getElementById("random-candidates"),
    runExperimentButton: document.getElementById("run-experiment-button"),
    status: document.getElementById("status"),
    experimentSummary: document.getElementById("experiment-summary"),
    standardBody: document.getElementById("standard-body"),
    generalizationBody: document.getElementById("generalization-body"),
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
  const progressCanvas = document.getElementById("ga-progress-canvas");
  const progressCtx = progressCanvas.getContext("2d");
  const state = { config: null, result: null };

  function applyPreset(presetName) {
    const preset = state.config.experiment_presets[presetName];
    if (!preset) {
      return;
    }
    elements.suite.value = preset.suite;
    elements.presetDescription.value = preset.description;
    Common.fillScenarioControls(elements, state.config, preset.settings);
    Common.setFitnessWeightValues(elements.fitnessWeights, preset.fitness_weights);
    Common.fillGaControls(elements.gaFields, state.config, preset.ga_settings);
    elements.randomCandidates.value = preset.random_candidates;
    elements.evaluationSeeds.value = preset.evaluation_seeds.join(", ");
  }

  function payload() {
    const gaSettings = Common.readGaSettings(elements.gaFields);
    return {
      preset: elements.preset.value,
      suite: elements.suite.value,
      settings: Common.readScenarioPayload(elements),
      evaluation_seeds: Common.parseSeedList(elements.evaluationSeeds.value, state.config.default_evaluation_seeds),
      fitness_weights: Common.readFitnessWeights(elements.fitnessWeights),
      ga_settings: gaSettings,
      random_candidates: Number(elements.randomCandidates.value),
    };
  }

  function render() {
    if (!state.result) {
      Common.renderMethodSummaryTable(elements.standardBody, []);
      Common.renderGeneralizationTable(elements.generalizationBody, null);
      Common.drawLineChart(progressCtx, progressCanvas, [], -1, "GA convergence appears here after an experiment run.");
      return;
    }
    const standardMethods = [
      state.result.standard.default,
      ...state.result.standard.heuristics,
      state.result.standard.random,
      state.result.standard.ga,
    ];
    Common.renderMethodSummaryTable(elements.standardBody, standardMethods);
    Common.renderGeneralizationTable(elements.generalizationBody, state.result.generalization || null);
    Common.drawLineChart(progressCtx, progressCanvas, state.result.standard.ga_history.map((entry) => entry.best_fitness), state.result.standard.ga_history.length - 1, "GA convergence appears here after an experiment run.");
  }

  async function runExperiment() {
    elements.runExperimentButton.disabled = true;
    Common.setStatus(elements.status, "Running experiment...");
    try {
      const response = await fetch("/api/experiments/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload()),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Experiment request failed.");
      }
      state.result = result;
      render();
      elements.experimentSummary.textContent = `Ran the ${result.suite} suite with preset ${result.preset || "custom"} and ${result.evaluation_seeds.length} evaluation seeds.`;
      Common.setStatus(elements.status, "Experiment complete.");
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    } finally {
      elements.runExperimentButton.disabled = false;
    }
  }

  elements.preset.addEventListener("change", () => applyPreset(elements.preset.value));
  elements.runExperimentButton.addEventListener("click", runExperiment);

  state.config = await Common.fetchConfig();
  Common.populatePresetSelect(elements.preset, state.config.experiment_presets);
  Common.populateLayoutSelect(elements.layout, state.config);
  Common.buildFitnessWeightControls(elements.fitnessWeights, state.config.default_fitness_weights);
  applyPreset(elements.preset.value);
  render();
  Common.setStatus(elements.status, "Ready.");
});
