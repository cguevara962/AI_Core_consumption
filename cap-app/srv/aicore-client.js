'use strict';
const axios = require('axios');

/**
 * Fetches an OAuth2 token from SAP AI Core.
 */
async function getToken() {
  const { AICORE_TOKEN_URL, AICORE_CLIENT_ID, AICORE_CLIENT_SECRET } = process.env;
  const resp = await axios.post(
    `${AICORE_TOKEN_URL}/oauth/token`,
    new URLSearchParams({ grant_type: 'client_credentials',
                          client_id: AICORE_CLIENT_ID,
                          client_secret: AICORE_CLIENT_SECRET }),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  return resp.data.access_token;
}

/**
 * Calls the AI Core inference endpoint for material consumption prediction.
 * @param {Array} instances  Array of { material_id, date, is_holiday, is_weekend, is_payday, lag_7d, lag_14d, lag_28d, rolling_4w_avg }
 * @returns {Array} predictions
 */
async function predictConsumption(instances) {
  const token = await getToken();
  const { AICORE_DEPLOYMENT_URL, AICORE_RESOURCE_GROUP = 'default' } = process.env;

  const resp = await axios.post(
    `${AICORE_DEPLOYMENT_URL}/v2/models/consumption-model/infer`,
    { inputs: [{ data: instances }] },
    {
      headers: {
        Authorization      : `Bearer ${token}`,
        'AI-Resource-Group': AICORE_RESOURCE_GROUP,
        'Content-Type'     : 'application/json',
      },
    }
  );
  return resp.data.outputs[0].data;
}

module.exports = { predictConsumption };
