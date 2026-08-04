namespace consumption;
using { cuid, managed } from '@sap/cds/common';

entity Materials {
  key ID        : String(40);
      name      : String(100);
      unit      : String(10);
}

entity ConsumptionHistory {
  key ID         : UUID;
      material   : Association to Materials;
      date       : Date;
      quantity   : Decimal(12, 3);
      unit       : String(10);
      isHoliday  : Boolean default false;
      isWeekend  : Boolean default false;
      isPayday   : Boolean default false;
      dayOfWeek  : Integer;
      month      : Integer;
      weekOfYear : Integer;
      year       : Integer;
}

entity MaterialPredictions {
  key ID             : UUID;
      material       : Association to Materials;
      predictionDate : Date;
      predictedQty   : Decimal(12, 3);
      isHoliday      : Boolean default false;
      isWeekend      : Boolean default false;
      isPayday       : Boolean default false;
      generatedAt    : DateTime;
}
