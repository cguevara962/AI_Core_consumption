using consumption from '../db/schema';

service ConsumptionService @(path:'/consumption') {

  @readonly entity Materials           as projection on consumption.Materials;
  @readonly entity ConsumptionHistory  as projection on consumption.ConsumptionHistory
    { *, material.name as materialName, material.unit as materialUnit };
  @readonly entity MaterialPredictions as projection on consumption.MaterialPredictions
    { *, material.name as materialName, material.unit as materialUnit };

  /**
   * Calls AI Core inference endpoint and stores today's predictions.
   * Requires AICORE_* env vars (see .env.example).
   */
  action refreshPredictions() returns array of MaterialPredictions;
}
