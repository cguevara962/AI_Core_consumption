using ConsumptionService from '../../srv/consumption-service';

annotate ConsumptionService.MaterialPredictions with @(

  UI.HeaderInfo: {
    TypeName      : 'Prediction',
    TypeNamePlural: 'Material Predictions',
    Title         : { Value: materialName },
    Description   : { Value: predictionDate }
  },

  UI.SelectionFields: [ material_ID, predictionDate ],

  UI.LineItem: [
    { $Type: 'UI.DataField', Value: materialName,   Label: 'Material'            },
    { $Type: 'UI.DataField', Value: material_ID,    Label: 'Material ID'          },
    { $Type: 'UI.DataField', Value: predictionDate, Label: 'Prediction Date'      },
    { $Type: 'UI.DataField', Value: predictedQty,   Label: 'Predicted Quantity'   },
    { $Type: 'UI.DataField', Value: materialUnit,   Label: 'Unit'                 },
    { $Type: 'UI.DataField', Value: isHoliday,      Label: 'Holiday'              },
    { $Type: 'UI.DataField', Value: isWeekend,      Label: 'Weekend'              },
    { $Type: 'UI.DataField', Value: isPayday,       Label: 'Payday'               },
    { $Type: 'UI.DataField', Value: generatedAt,    Label: 'Generated At'         }
  ]
);
