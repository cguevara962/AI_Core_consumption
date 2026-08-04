using ConsumptionService from '../../srv/consumption-service';

annotate ConsumptionService.ConsumptionHistory with @(

  UI.HeaderInfo: {
    TypeName      : 'Consumption Record',
    TypeNamePlural: 'Consumption History',
    Title         : { Value: materialName },
    Description   : { Value: date }
  },

  UI.SelectionFields: [
    material_ID, date, isHoliday, isWeekend, isPayday, year, month
  ],

  UI.LineItem: [
    { $Type: 'UI.DataField', Value: materialName,  Label: 'Material'  },
    { $Type: 'UI.DataField', Value: material_ID,   Label: 'Material ID' },
    { $Type: 'UI.DataField', Value: date,           Label: 'Date'      },
    { $Type: 'UI.DataField', Value: quantity,       Label: 'Quantity'  },
    { $Type: 'UI.DataField', Value: materialUnit,   Label: 'Unit'      },
    { $Type: 'UI.DataField', Value: year,           Label: 'Year'      },
    { $Type: 'UI.DataField', Value: month,          Label: 'Month'     },
    { $Type: 'UI.DataField', Value: isHoliday,      Label: 'Holiday'   },
    { $Type: 'UI.DataField', Value: isWeekend,      Label: 'Weekend'   },
    { $Type: 'UI.DataField', Value: isPayday,       Label: 'Payday'    }
  ]
);
