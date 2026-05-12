document.addEventListener("DOMContentLoaded", () => {
  const Common = window.AppCommon;
  const elements = {
    runButton: document.getElementById("run-checkpoint-button"),
    animationButton: document.getElementById("generate-animations-button"),
    status: document.getElementById("checkpoint-status"),
    settingsBox: document.getElementById("settings-box"),
    summaryBody: document.getElementById("checkpoint-summary-body"),
    insights: document.getElementById("checkpoint-insights"),
    plots: document.getElementById("checkpoint-plots"),
    animations: document.getElementById("checkpoint-animations"),
    notes: document.getElementById("checkpoint-notes"),
  };

  const methodLabels = {
    fixed_default: "Fixed default",
    random_search: "Random search",
    ga_no_fairness: "GA no fairness",
    ga_fairness: "GA fairness",
  };

  function label(method) {
    return methodLabels[method] || method;
  }

  function formatParams(params) {
    return `[${params.map((value) => Number(value).toFixed(2)).join(", ")}]`;
  }

  function renderSettings(result) {
    const settings = result.settings;
    const exitWidth = result.layout_definition ? result.layout_definition.exit_width : 0.6;
    elements.settingsBox.innerHTML = `
      <strong>Scenario:</strong> ${settings.layout} layout, fixed door width ${exitWidth}, ${settings.num_high} high-mobility agents, ${settings.num_low} low-mobility agents, max_ticks ${settings.max_ticks}, dt ${settings.dt}.<br>
      <strong>Seeds:</strong> [${result.seeds.join(", ")}].<br>
      <strong>Search:</strong> random search ${result.random_search.num_samples} samples, GA population ${result.ga_settings.population_size}, GA generations ${result.ga_settings.generations}.`;
  }

  function renderSummary(result) {
    elements.summaryBody.innerHTML = result.methods.map((entry) => `
      <tr>
        <td>${label(entry.method)}</td>
        <td>${Common.formatMetric(entry.fitness, 3)}</td>
        <td>${Common.formatMetric(entry.total_time, 3)}</td>
        <td>${Common.formatMetric(entry.fairness_gap_time, 3)}</td>
        <td>${Common.formatMetric(entry.mean_congestion, 3)}</td>
        <td>${Common.formatMetric(entry.near_collisions, 3)}</td>
        <td>${Common.formatMetric(entry.remaining_agents, 3)}</td>
        <td>${entry.all_evacuated ? "yes" : "no"}</td>
        <td class="param-cell">${formatParams(entry.best_params)}</td>
      </tr>
    `).join("");
  }

  function minBy(entries, key) {
    return entries.reduce((best, entry) => entry[key] < best[key] ? entry : best, entries[0]);
  }

  function renderInsights(result) {
    const methods = result.methods;
    const bestFitness = minBy(methods, "fitness");
    const fastest = minBy(methods, "total_time");
    const fairnessCandidates = methods.filter((entry) => entry.fairness_gap_time !== null && entry.fairness_gap_time !== undefined);
    const bestFairness = fairnessCandidates.length ? minBy(fairnessCandidates, "fairness_gap_time") : null;
    const noFair = methods.find((entry) => entry.method === "ga_no_fairness");
    const fair = methods.find((entry) => entry.method === "ga_fairness");
    const allEvacuated = methods.every((entry) => entry.all_evacuated);
    let fairComparison = "Both GA variants are available after the run.";
    if (noFair && fair) {
      const gapDelta = fair.fairness_gap_time - noFair.fairness_gap_time;
      const timeDelta = fair.total_time - noFair.total_time;
      fairComparison = `Adding the fairness penalty changed the GA fairness gap by ${Common.formatMetric(gapDelta, 3)}s and total time by ${Common.formatMetric(timeDelta, 3)}s relative to GA without fairness.`;
    }

    elements.insights.innerHTML = `
      <div class="summary-card"><strong>Best common fitness:</strong><br>${label(bestFitness.method)} (${Common.formatMetric(bestFitness.fitness, 3)}).</div>
      <div class="summary-card"><strong>Fastest evacuation:</strong><br>${label(fastest.method)} (${Common.formatMetric(fastest.total_time, 3)}s).</div>
      <div class="summary-card"><strong>Smallest fairness gap:</strong><br>${bestFairness ? `${label(bestFairness.method)} (${Common.formatMetric(bestFairness.fairness_gap_time, 3)}s).` : "No defined fairness gap."}</div>
      <div class="summary-card"><strong>Evacuation completion:</strong><br>${allEvacuated ? "All methods evacuated all agents across all seeds." : "At least one method left agents unevacuated; check remaining_agents."}</div>
      <div class="summary-card full-width"><strong>GA fairness comparison:</strong><br>${fairComparison}</div>
      <div class="summary-card full-width"><strong>Output files:</strong><br>${Object.values(result.outputs).map((path) => `<code>${path}</code>`).join("<br>")}</div>
    `;
  }

  function renderPlots(result) {
    const plots = [
      ["convergence_png", "GA convergence"],
      ["method_comparison_png", "Method comparison"],
      ["group_times_png", "Group times"],
      ["efficiency_fairness_tradeoff_png", "Efficiency-fairness tradeoff"],
    ];
    const timestamp = Date.now();
    elements.plots.innerHTML = plots.map(([key, title]) => {
      const url = result.plot_urls[key];
      if (!url) {
        return "";
      }
      return `<figure class="plot-card"><figcaption>${title}</figcaption><img src="${url}?t=${timestamp}" alt="${title}"></figure>`;
    }).join("");
  }

  function renderAnimations(result) {
    const timestamp = Date.now();
    const figures = [];
    if (result.animation_urls.side_by_side) {
      figures.push([result.animation_urls.side_by_side, `Side-by-side comparison, seed ${result.seed}`]);
    }
    Object.entries(result.animation_urls.individual).forEach(([method, url]) => {
      figures.push([url, `${label(method)}, seed ${result.seed}`]);
    });
    elements.animations.innerHTML = figures.map(([url, title]) => `
      <figure class="plot-card">
        <figcaption>${title}</figcaption>
        <img src="${url}?t=${timestamp}" alt="${title}">
      </figure>
    `).join("");
  }

  function render(result) {
    renderSettings(result);
    renderSummary(result);
    renderInsights(result);
    renderPlots(result);
    elements.notes.textContent = result.notes;
  }

  async function runCheckpoint() {
    elements.runButton.disabled = true;
    Common.setStatus(elements.status, "Running checkpoint experiment and generating plots...");
    try {
      const response = await fetch("/api/checkpoint/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Checkpoint run failed.");
      }
      render(result);
      Common.setStatus(elements.status, "Checkpoint experiment complete. Results saved in results/checkpoint/.");
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    } finally {
      elements.runButton.disabled = false;
    }
  }

  async function generateAnimations() {
    elements.animationButton.disabled = true;
    Common.setStatus(elements.status, "Generating GIFs from checkpoint best runs...");
    try {
      const response = await fetch("/api/checkpoint/animate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed: 0, format: "gif", fps: 12 }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Animation generation failed.");
      }
      renderAnimations(result);
      Common.setStatus(elements.status, "GIF generation complete. Animations saved in results/checkpoint/animations/.");
    } catch (error) {
      Common.setStatus(elements.status, error.message);
    } finally {
      elements.animationButton.disabled = false;
    }
  }

  elements.runButton.addEventListener("click", runCheckpoint);
  elements.animationButton.addEventListener("click", generateAnimations);
});
