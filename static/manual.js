document.addEventListener("DOMContentLoaded", async () => {
  const Common = window.AppCommon;
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
  const canvas = document.getElementById("sim-canvas");
  const ctx = canvas.getContext("2d");
  const playback = Common.createPlayback(ctx, canvas);
  const state = { result: null, config: null };

  function payload() {
    return {
      ...Common.readScenarioPayload(elements),
      params: Common.readParamValues(elements.params),
    };
  }

  async function runSimulation() {
    elements.runButton.disabled = true;
    Common.setStatus(elements.status, "Running simulation...");
    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload()),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Simulation request failed.");
      }
      state.result = result;
      Common.updateMetrics(elements.metrics, result);
      playback.play(result);
      Common.setStatus(elements.status, result.all_evacuated ? "Simulation complete." : "Simulation reached max ticks.");
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    } finally {
      elements.runButton.disabled = false;
    }
  }

  elements.runButton.addEventListener("click", runSimulation);
  elements.replayButton.addEventListener("click", () => playback.play(state.result));

  state.config = await Common.fetchConfig();
  Common.fillScenarioControls(elements, state.config);
  Common.buildParamControls(elements.params, state.config);
  Common.setStatus(elements.status, "Ready.");
});
