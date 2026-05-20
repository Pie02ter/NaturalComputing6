(function () {
  const Common = {};

  Common.fetchConfig = async function fetchConfig() {
    const response = await fetch("/api/config");
    if (!response.ok) {
      throw new Error("Failed to load configuration.");
    }
    return response.json();
  };

  Common.setStatus = function setStatus(element, message) {
    if (element) {
      element.textContent = message;
    }
  };

  Common.formatMetric = function formatMetric(value, digits = 2) {
    if (value === null || value === undefined) {
      return "-";
    }
    if (typeof value === "number") {
      return Number.isInteger(value) ? `${value}` : value.toFixed(digits);
    }
    return `${value}`;
  };

  Common.markActiveNav = function markActiveNav() {
    const currentPath = window.location.pathname;
    document.querySelectorAll("[data-nav]").forEach((link) => {
      if (link.getAttribute("href") === currentPath) {
        link.classList.add("active");
      }
    });
  };

  Common.populateLayoutSelect = function populateLayoutSelect(select, config) {
    if (!select) {
      return;
    }
    select.innerHTML = "";
    Object.keys(config.layouts).forEach((layoutName) => {
      const option = document.createElement("option");
      option.value = layoutName;
      option.textContent = layoutName;
      select.appendChild(option);
    });
  };

  Common.fillScenarioControls = function fillScenarioControls(elements, config, overrides = {}) {
    Common.populateLayoutSelect(elements.layout, config);
    const values = { ...config.defaults, ...overrides };
    elements.layout.value = values.layout;
    elements.seed.value = values.seed;
    elements.numHigh.value = values.num_high;
    elements.numLow.value = values.num_low;
    elements.maxTicks.value = values.max_ticks;
    elements.dt.value = values.dt;
  };

  Common.readScenarioPayload = function readScenarioPayload(elements) {
    return {
      layout: elements.layout.value,
      seed: Number(elements.seed.value),
      num_high: Number(elements.numHigh.value),
      num_low: Number(elements.numLow.value),
      max_ticks: Number(elements.maxTicks.value),
      dt: Number(elements.dt.value),
    };
  };

  Common.buildParamControls = function buildParamControls(container, config, initialParams) {
    if (!container) {
      return;
    }
    const values = initialParams || config.default_params;
    container.innerHTML = "";
    config.param_names.forEach((name, index) => {
      const [min, max] = config.param_bounds[index];
      const value = values[index];
      const row = document.createElement("label");
      row.className = "param-row";
      row.innerHTML = `<div class="param-header"><span>${name}</span><span id="param-value-${index}">${Number(value).toFixed(2)}</span></div>`;
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
      row.appendChild(slider);
      container.appendChild(row);
    });
  };

  Common.readParamValues = function readParamValues(container) {
    return Array.from(container.querySelectorAll("input[type='range']")).map((slider) => Number(slider.value));
  };

  Common.buildGaParamControls = function buildGaParamControls(container, config, initialParams) {
    if (!container || !config.ga_param_names || !config.ga_param_bounds) {
      return;
    }
    const names = config.ga_param_names;
    const bounds = config.ga_param_bounds;
    const values = initialParams || config.default_ga_seed_vector || [];
    container.innerHTML = "";
    names.forEach((name, index) => {
      const [min, max] = bounds[index];
      const value = values[index] ?? min;
      const row = document.createElement("label");
      row.className = "param-row";
      row.innerHTML = `<div class="param-header"><span>${name}</span><span id="ga-param-value-${index}">${Number(value).toFixed(2)}</span></div>`;
      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = min;
      slider.max = max;
      slider.step = "0.05";
      slider.value = value;
      slider.dataset.gaIndex = index;
      slider.addEventListener("input", (event) => {
        const idx = event.target.dataset.gaIndex;
        document.getElementById(`ga-param-value-${idx}`).textContent = Number(event.target.value).toFixed(2);
      });
      row.appendChild(slider);
      container.appendChild(row);
    });
  };

  Common.readGaParamValues = function readGaParamValues(container) {
    if (!container) {
      return [];
    }
    return Array.from(container.querySelectorAll("input[type='range']")).map((slider) => Number(slider.value));
  };

  Common.renderFixedWallSummary = function renderFixedWallSummary(element, config) {
    if (!element || !config.fixed_wall_params) {
      return;
    }
    const w = config.fixed_wall_params;
    element.textContent = `Fixed during GA: wall_rep_weight = ${w.wall_rep_weight}, wall_radius = ${w.wall_radius}`;
  };

  Common.buildFitnessWeightControls = function buildFitnessWeightControls(container, weights) {
    if (!container) {
      return;
    }
    container.innerHTML = "";
    Object.entries(weights).forEach(([key, value]) => {
      const label = document.createElement("label");
      label.innerHTML = `${key}<input data-weight="${key}" type="number" step="0.01" value="${value}">`;
      container.appendChild(label);
    });
  };

  Common.setFitnessWeightValues = function setFitnessWeightValues(container, weights) {
    Object.entries(weights).forEach(([key, value]) => {
      const input = container.querySelector(`[data-weight='${key}']`);
      if (input) {
        input.value = value;
      }
    });
  };

  Common.readFitnessWeights = function readFitnessWeights(container) {
    const weights = {};
    container.querySelectorAll("[data-weight]").forEach((input) => {
      weights[input.dataset.weight] = Number(input.value);
    });
    return weights;
  };

  Common.fillGaControls = function fillGaControls(fields, config, overrides = {}) {
    const values = { ...config.ga_defaults, ...overrides };
    fields.populationSize.value = values.population_size;
    fields.generations.value = values.generations;
    fields.eliteCount.value = values.elite_count;
    fields.tournamentSize.value = values.tournament_size;
    fields.crossoverProbability.value = values.crossover_probability;
    fields.mutationProbability.value = values.mutation_probability;
    fields.mutationSigmaScale.value = values.mutation_sigma_scale;
    fields.rngSeed.value = values.rng_seed !== undefined ? values.rng_seed : 123;
  };

  Common.readGaSettings = function readGaSettings(fields) {
    return {
      population_size: Number(fields.populationSize.value),
      generations: Number(fields.generations.value),
      elite_count: Number(fields.eliteCount.value),
      tournament_size: Number(fields.tournamentSize.value),
      crossover_probability: Number(fields.crossoverProbability.value),
      mutation_probability: Number(fields.mutationProbability.value),
      mutation_sigma_scale: Number(fields.mutationSigmaScale.value),
      rng_seed: Number(fields.rngSeed.value),
    };
  };

  Common.parseSeedList = function parseSeedList(text, fallback = []) {
    const values = String(text || "")
      .split(",")
      .map((value) => value.trim())
      .filter((value) => value.length > 0)
      .map((value) => Number(value))
      .filter((value) => !Number.isNaN(value));
    return values.length ? values : fallback;
  };

  Common.updateMetrics = function updateMetrics(metricElements, result) {
    metricElements.ticks.textContent = Common.formatMetric(result.ticks);
    metricElements.time.textContent = Common.formatMetric(result.total_time);
    metricElements.evacuated.textContent = Common.formatMetric(result.evacuated_agents);
    metricElements.remaining.textContent = Common.formatMetric(result.remaining_agents);
    metricElements.collisions.textContent = Common.formatMetric(result.near_collisions);
    metricElements.congestion.textContent = Common.formatMetric(result.mean_congestion);
    metricElements.high.textContent = Common.formatMetric(result.mean_high_time);
    metricElements.low.textContent = Common.formatMetric(result.mean_low_time);
    metricElements.gap.textContent = Common.formatMetric(result.fairness_gap_time);
  };

  Common.drawFrameOnCanvas = function drawFrameOnCanvas(targetCtx, targetCanvas, result, frame) {
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
    Common.drawRoomWithDoor(targetCtx, result, scale, offsetX, offsetY);

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
  };

  Common.createPlayback = function createPlayback(targetCtx, targetCanvas) {
    let handle = null;
    function stop() {
      if (handle !== null) {
        cancelAnimationFrame(handle);
        handle = null;
      }
    }
    function play(result) {
      stop();
      if (!result || !result.frames || !result.frames.length) {
        return;
      }
      let index = 0;
      let lastTime = 0;
      const render = (timestamp) => {
        if (timestamp - lastTime > 90) {
          Common.drawFrameOnCanvas(targetCtx, targetCanvas, result, result.frames[index]);
          index += 1;
          lastTime = timestamp;
        }
        if (index < result.frames.length) {
          handle = requestAnimationFrame(render);
        } else {
          handle = null;
        }
      };
      handle = requestAnimationFrame(render);
    }
    return { play, stop };
  };

  Common.inferExitSide = function inferExitSide(result) {
    const roomWidth = result.room_size[0];
    const roomHeight = result.room_size[1];
    const [exitX, exitY] = result.exit_pos;
    const distances = {
      left: Math.abs(exitX),
      right: Math.abs(roomWidth - exitX),
      bottom: Math.abs(exitY),
      top: Math.abs(roomHeight - exitY),
    };
    return Object.entries(distances).sort((a, b) => a[1] - b[1])[0][0];
  };

  Common.resultExits = function resultExits(result) {
    if (result.exits && result.exits.length) {
      return result.exits;
    }
    return [
      {
        pos: result.exit_pos,
        width: result.exit_width || 0.2,
        side: result.exit_side || Common.inferExitSide(result),
      },
    ];
  };

  Common.mergeIntervals = function mergeIntervals(intervals) {
    if (!intervals.length) {
      return [];
    }
    const ordered = [...intervals].sort((a, b) => a[0] - b[0]);
    const merged = [[ordered[0][0], ordered[0][1]]];
    ordered.slice(1).forEach(([start, end]) => {
      const last = merged[merged.length - 1];
      if (start <= last[1]) {
        last[1] = Math.max(last[1], end);
      } else {
        merged.push([start, end]);
      }
    });
    return merged;
  };

  Common.doorIntervalsOnSide = function doorIntervalsOnSide(exits, side, roomWidth, roomHeight) {
    const intervals = [];
    exits.forEach((exitInfo) => {
      if (exitInfo.side !== side) {
        return;
      }
      const halfWidth = (exitInfo.width || 0.2) * 0.5;
      const [posX, posY] = exitInfo.pos;
      if (side === "left" || side === "right") {
        intervals.push([Math.max(0, posY - halfWidth), Math.min(roomHeight, posY + halfWidth)]);
      } else {
        intervals.push([Math.max(0, posX - halfWidth), Math.min(roomWidth, posX + halfWidth)]);
      }
    });
    return Common.mergeIntervals(intervals);
  };

  Common.drawRoomWithDoor = function drawRoomWithDoor(targetCtx, result, scale, offsetX, offsetY) {
    const roomWidth = result.room_size[0];
    const roomHeight = result.room_size[1];
    const exits = Common.resultExits(result);
    const sx = (x) => offsetX + x * scale;
    const sy = (y) => offsetY + (roomHeight - y) * scale;

    function segment(x1, y1, x2, y2, color, width) {
      targetCtx.beginPath();
      targetCtx.strokeStyle = color;
      targetCtx.lineWidth = width;
      targetCtx.lineCap = "round";
      targetCtx.moveTo(sx(x1), sy(y1));
      targetCtx.lineTo(sx(x2), sy(y2));
      targetCtx.stroke();
    }

    function wall(x1, y1, x2, y2) {
      segment(x1, y1, x2, y2, "#334155", 2);
    }

    function door(x1, y1, x2, y2, width) {
      segment(x1, y1, x2, y2, "#16a34a", Math.max(4, width * scale));
    }

    function drawSide(side, wallFn, doorFn, spanStart, spanEnd) {
      const gaps = Common.doorIntervalsOnSide(exits, side, roomWidth, roomHeight);
      let cursor = spanStart;
      gaps.forEach(([gapStart, gapEnd]) => {
        if (gapStart > cursor) {
          wallFn(cursor, gapStart);
        }
        doorFn(gapStart, gapEnd);
        cursor = gapEnd;
      });
      if (cursor < spanEnd) {
        wallFn(cursor, spanEnd);
      }
    }

    drawSide(
      "bottom",
      (a, b) => wall(a, 0, b, 0),
      (a, b) => {
        const exitWidth = exits.find((exitInfo) => exitInfo.side === "bottom")?.width || 0.2;
        door(a, 0, b, 0, exitWidth);
      },
      0,
      roomWidth,
    );
    drawSide(
      "top",
      (a, b) => wall(a, roomHeight, b, roomHeight),
      (a, b) => {
        const exitWidth = exits.find((exitInfo) => exitInfo.side === "top")?.width || 0.2;
        door(a, roomHeight, b, roomHeight, exitWidth);
      },
      0,
      roomWidth,
    );
    drawSide(
      "left",
      (a, b) => wall(0, a, 0, b),
      (a, b) => {
        const exitWidth = exits.find((exitInfo) => exitInfo.side === "left")?.width || 0.2;
        door(0, a, 0, b, exitWidth);
      },
      0,
      roomHeight,
    );
    drawSide(
      "right",
      (a, b) => wall(roomWidth, a, roomWidth, b),
      (a, b) => {
        const exitWidth = exits.find((exitInfo) => exitInfo.side === "right")?.width || 0.2;
        door(roomWidth, a, roomWidth, b, exitWidth);
      },
      0,
      roomHeight,
    );

    (result.internal_walls || []).forEach((segment) => {
      const [start, end] = segment;
      wall(start[0], start[1], end[0], end[1]);
    });
  };

  Common.playSynchronizedResults = function playSynchronizedResults(entries) {
    if (!entries.length) {
      return;
    }
    let index = 0;
    let lastTime = 0;
    const maxFrames = Math.max(...entries.map((entry) => entry.result.frames.length));
    const render = (timestamp) => {
      if (timestamp - lastTime > 90) {
        entries.forEach((entry) => {
          const frame = entry.result.frames[Math.min(index, entry.result.frames.length - 1)];
          Common.drawFrameOnCanvas(entry.ctx, entry.canvas, entry.result, frame);
        });
        index += 1;
        lastTime = timestamp;
      }
      if (index < maxFrames) {
        requestAnimationFrame(render);
      }
    };
    requestAnimationFrame(render);
  };

  Common.drawLineChart = function drawLineChart(targetCtx, targetCanvas, values, selectedIndex, emptyText) {
    targetCtx.clearRect(0, 0, targetCanvas.width, targetCanvas.height);
    targetCtx.fillStyle = "#f8fafc";
    targetCtx.fillRect(0, 0, targetCanvas.width, targetCanvas.height);
    if (!values.length) {
      targetCtx.fillStyle = "#526077";
      targetCtx.font = "14px Arial";
      targetCtx.fillText(emptyText, 20, 30);
      return;
    }
    const padding = { top: 20, right: 20, bottom: 36, left: 48 };
    const width = targetCanvas.width - padding.left - padding.right;
    const height = targetCanvas.height - padding.top - padding.bottom;
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = Math.max(maxValue - minValue, 1e-6);

    targetCtx.strokeStyle = "#cbd5e1";
    targetCtx.beginPath();
    targetCtx.moveTo(padding.left, padding.top + height);
    targetCtx.lineTo(padding.left + width, padding.top + height);
    targetCtx.moveTo(padding.left, padding.top);
    targetCtx.lineTo(padding.left, padding.top + height);
    targetCtx.stroke();

    targetCtx.strokeStyle = "#7c3aed";
    targetCtx.lineWidth = 2;
    targetCtx.beginPath();
    values.forEach((value, index) => {
      const x = padding.left + (values.length === 1 ? width / 2 : (index / (values.length - 1)) * width);
      const y = padding.top + height - ((value - minValue) / valueRange) * height;
      if (index === 0) {
        targetCtx.moveTo(x, y);
      } else {
        targetCtx.lineTo(x, y);
      }
    });
    targetCtx.stroke();

    values.forEach((value, index) => {
      const x = padding.left + (values.length === 1 ? width / 2 : (index / (values.length - 1)) * width);
      const y = padding.top + height - ((value - minValue) / valueRange) * height;
      targetCtx.beginPath();
      targetCtx.fillStyle = index === selectedIndex ? "#dc2626" : "#2563eb";
      targetCtx.arc(x, y, index === selectedIndex ? 5 : 3.5, 0, Math.PI * 2);
      targetCtx.fill();
    });

    targetCtx.fillStyle = "#0f172a";
    targetCtx.font = "12px Arial";
    targetCtx.fillText(`Best ${minValue.toFixed(2)}`, 10, padding.top + 10);
    targetCtx.fillText(`Worst ${maxValue.toFixed(2)}`, 10, padding.top + 26);
  };

  Common.drawBarChart = function drawBarChart(targetCtx, targetCanvas, items, emptyText) {
    targetCtx.clearRect(0, 0, targetCanvas.width, targetCanvas.height);
    targetCtx.fillStyle = "#f8fafc";
    targetCtx.fillRect(0, 0, targetCanvas.width, targetCanvas.height);
    if (!items.length) {
      targetCtx.fillStyle = "#526077";
      targetCtx.font = "14px Arial";
      targetCtx.fillText(emptyText, 20, 30);
      return;
    }
    const padding = { top: 20, right: 20, bottom: 60, left: 50 };
    const width = targetCanvas.width - padding.left - padding.right;
    const height = targetCanvas.height - padding.top - padding.bottom;
    const maxValue = Math.max(...items.map((item) => item.fitness), 1);
    const barWidth = width / items.length * 0.62;
    targetCtx.strokeStyle = "#cbd5e1";
    targetCtx.beginPath();
    targetCtx.moveTo(padding.left, padding.top + height);
    targetCtx.lineTo(padding.left + width, padding.top + height);
    targetCtx.moveTo(padding.left, padding.top);
    targetCtx.lineTo(padding.left, padding.top + height);
    targetCtx.stroke();
    items.forEach((item, index) => {
      const x = padding.left + (index + 0.2) * (width / items.length);
      const barHeight = (item.fitness / maxValue) * height;
      const y = padding.top + height - barHeight;
      targetCtx.fillStyle = item.method === "ga" || item.method === "ga_best" ? "#7c3aed" : item.method === "default" ? "#0f766e" : "#2563eb";
      targetCtx.fillRect(x, y, barWidth, barHeight);
      targetCtx.fillStyle = "#0f172a";
      targetCtx.font = "12px Arial";
      targetCtx.fillText(item.fitness.toFixed(1), x, y - 6);
      targetCtx.save();
      targetCtx.translate(x + barWidth / 2, padding.top + height + 18);
      targetCtx.rotate(-0.4);
      targetCtx.fillText(item.method, -20, 0);
      targetCtx.restore();
    });
  };

  Common.renderHistoryTable = function renderHistoryTable(tbody, history) {
    if (!tbody) {
      return;
    }
    if (!history.length) {
      tbody.innerHTML = '<tr><td colspan="3">No GA history available.</td></tr>';
      return;
    }
    tbody.innerHTML = history.map((entry) => {
      const params = entry.best_params.map((value) => Number(value).toFixed(2)).join(", ");
      return `<tr><td>${entry.generation}</td><td>${entry.best_fitness.toFixed(3)}</td><td class="param-cell">[${params}]</td></tr>`;
    }).join("");
  };

  Common.renderMethodSummaryTable = function renderMethodSummaryTable(tbody, methods) {
    if (!tbody) {
      return;
    }
    if (!methods.length) {
      tbody.innerHTML = '<tr><td colspan="5">No comparison results available.</td></tr>';
      return;
    }
    tbody.innerHTML = methods.map((method) => {
      const params = (method.params || []).map((value) => Number(value).toFixed(2)).join(", ");
      return `<tr><td>${method.method}</td><td>${Common.formatMetric(method.fitness, 3)}</td><td>${Common.formatMetric(method.total_time)}</td><td>${Common.formatMetric(method.fairness_gap_time)}</td><td class="param-cell">[${params}]</td></tr>`;
    }).join("");
  };

  Common.renderGeneralizationTable = function renderGeneralizationTable(tbody, generalization) {
    if (!tbody) {
      return;
    }
    if (!generalization || !Object.keys(generalization).length) {
      tbody.innerHTML = '<tr><td colspan="6">Generalization output appears here for the generalization suite.</td></tr>';
      return;
    }
    const methods = ["default", "heuristic_1", "heuristic_2", "random_best", "ga_best"];
    tbody.innerHTML = Object.entries(generalization).map(([scenario, result]) => {
      const cells = methods.map((method) => `<td>${Common.formatMetric(result[method]?.fitness, 2)}</td>`).join("");
      return `<tr><td>${scenario}</td>${cells}</tr>`;
    }).join("");
  };

  Common.populatePresetSelect = function populatePresetSelect(select, presets) {
    if (!select) {
      return;
    }
    select.innerHTML = "";
    Object.entries(presets).forEach(([key, value]) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = value.label;
      select.appendChild(option);
    });
  };

  document.addEventListener("DOMContentLoaded", Common.markActiveNav);
  window.AppCommon = Common;
})();
