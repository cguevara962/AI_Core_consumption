'use strict';
const cds = require('@sap/cds');
const { predictConsumption } = require('./aicore-client');

module.exports = cds.service.impl(async function () {
  const { ConsumptionHistory, MaterialPredictions, Materials } = this.entities;

  // ── refreshPredictions action ─────────────────────────────────────────────
  this.on('refreshPredictions', async (req) => {
    try {
      const today     = new Date().toISOString().split('T')[0];
      const todayDate = new Date(today);
      const isWeekend = [0, 6].includes(todayDate.getDay());
      const isPayday  = [1, 15].includes(todayDate.getDate());

      // Load all materials
      const materials = await SELECT.from(Materials);
      if (!materials.length) return req.error(400, 'No materials found in the database.');

      // Load recent 35 days of history for lag feature calculation
      const since = new Date(todayDate - 35 * 86400000).toISOString().split('T')[0];
      const history = await SELECT.from(ConsumptionHistory)
        .where({ date: { '>=': since } });

      // Build instances for AI Core
      const instances = materials.map(mat => {
        const mHist = history
          .filter(h => h.material_ID === mat.ID)
          .sort((a, b) => new Date(b.date) - new Date(a.date));

        const lag = (days) => {
          const target = new Date(todayDate - days * 86400000).toISOString().split('T')[0];
          return mHist.find(h => h.date === target)?.quantity ?? 0;
        };
        const rolling4wAvg = mHist.slice(0, 28)
          .reduce((s, h) => s + Number(h.quantity), 0) / Math.max(mHist.slice(0, 28).length, 1);

        return {
          material_id    : mat.ID,
          date           : today,
          is_holiday     : false,          // extend with a holiday calendar if needed
          is_weekend     : isWeekend,
          is_payday      : isPayday,
          lag_7d         : lag(7),
          lag_14d        : lag(14),
          lag_28d        : lag(28),
          rolling_4w_avg : rolling4wAvg,
        };
      });

      // Call AI Core
      const predictions = await predictConsumption(instances);

      // Upsert predictions for today
      await DELETE.from(MaterialPredictions).where({ predictionDate: today });
      const records = predictions
        .filter(p => !p.error)
        .map(p => ({
          ID             : cds.utils.uuid(),
          material_ID    : p.material_id,
          predictionDate : today,
          predictedQty   : p.predicted_quantity,
          isHoliday      : false,
          isWeekend,
          isPayday,
          generatedAt    : new Date().toISOString(),
        }));
      if (records.length) await INSERT.into(MaterialPredictions).entries(records);

      return SELECT.from(MaterialPredictions).where({ predictionDate: today });
    } catch (err) {
      console.error(err);
      return req.error(500, `Prediction failed: ${err.message}`);
    }
  });
});
