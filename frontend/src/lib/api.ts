import axios from 'axios';

const INGESTION_URL     = process.env.NEXT_PUBLIC_INGESTION_URL     || 'http://localhost:8001';
const VALIDATION_URL    = process.env.NEXT_PUBLIC_VALIDATION_URL    || 'http://localhost:8002';
const AI_URL            = process.env.NEXT_PUBLIC_AI_SERVICE_URL    || 'http://localhost:8004';
const ANALYTICS_URL     = process.env.NEXT_PUBLIC_ANALYTICS_URL     || 'http://localhost:8008';
const TRANSFORM_URL     = process.env.NEXT_PUBLIC_TRANSFORM_URL     || 'http://localhost:8003';
const NOTIFICATION_URL  = process.env.NEXT_PUBLIC_NOTIFICATION_URL  || 'http://localhost:8007';

const ingestionClient    = axios.create({ baseURL: INGESTION_URL });
const validationClient   = axios.create({ baseURL: VALIDATION_URL });
const aiClient           = axios.create({ baseURL: AI_URL });
const analyticsClient    = axios.create({ baseURL: ANALYTICS_URL });
const transformClient    = axios.create({ baseURL: TRANSFORM_URL });
const notificationClient = axios.create({ baseURL: NOTIFICATION_URL });

// ─── Ingestion API ────────────────────────────────────────────────────────────
export const ingestionApi = {
  getSources: (page = 1, pageSize = 20) =>
    ingestionClient.get('/api/v1/sources/', { params: { page, page_size: pageSize } }).then(r => r.data),

  createSource: (payload: Record<string, unknown>) =>
    ingestionClient.post('/api/v1/sources/', payload).then(r => r.data),

  getSource: (sourceId: string) =>
    ingestionClient.get(`/api/v1/sources/${sourceId}`).then(r => r.data),

  deleteSource: (sourceId: string) =>
    ingestionClient.delete(`/api/v1/sources/${sourceId}`).then(r => r.data),

  testConnection: (sourceId: string) =>
    ingestionClient.post(`/api/v1/sources/${sourceId}/test`).then(r => r.data),

  discoverSchema: (sourceId: string) =>
    ingestionClient.get(`/api/v1/sources/${sourceId}/schema`).then(r => r.data),

  previewSource: (sourceId: string, n = 10) =>
    ingestionClient.get(`/api/v1/sources/${sourceId}/preview`, { params: { n } }).then(r => r.data),

  getConnectorMarketplace: () =>
    ingestionClient.get('/api/v1/sources/connectors/marketplace').then(r => r.data),

  getJobs: (page = 1) =>
    ingestionClient.get('/api/v1/jobs/', { params: { page } }).then(r => r.data),

  getJob: (jobId: string) =>
    ingestionClient.get(`/api/v1/jobs/${jobId}`).then(r => r.data),

  triggerJob: (sourceId: string) =>
    ingestionClient.post('/api/v1/jobs/', { source_id: sourceId }).then(r => r.data),

  uploadFile: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return ingestionClient.post('/api/v1/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },
};

// ─── Validation API ───────────────────────────────────────────────────────────
export const validationApi = {
  validate: (records: Record<string, unknown>[], rules: Record<string, unknown>[]) =>
    validationClient.post('/api/v1/validation/validate', { records, rules }).then(r => r.data),

  getRules: (search = '') =>
    validationClient.get('/api/v1/validation/rules', { params: { search } }).then(r => r.data),

  getRuleDetail: (ruleType: string) =>
    validationClient.get(`/api/v1/validation/rules/${ruleType}`).then(r => r.data),

  detectSchema: (records: Record<string, unknown>[]) =>
    validationClient.post('/api/v1/validation/schema/detect', { records }).then(r => r.data),

  detectDuplicates: (records: Record<string, unknown>[], keyFields?: string[]) =>
    validationClient.post('/api/v1/validation/duplicates/detect', { records, key_fields: keyFields }).then(r => r.data),

  // Business rules
  createBusinessRule: (payload: Record<string, unknown>) =>
    validationClient.post('/api/v1/rules/', payload).then(r => r.data),

  listBusinessRules: (tenantId = 'default', domain = '') =>
    validationClient.get('/api/v1/rules/', { params: { tenant_id: tenantId, domain } }).then(r => r.data),

  deleteBusinessRule: (ruleId: string, tenantId = 'default') =>
    validationClient.delete(`/api/v1/rules/${ruleId}`, { params: { tenant_id: tenantId } }).then(r => r.data),

  evaluateBusinessRules: (records: Record<string, unknown>[], tenantId = 'default') =>
    validationClient.post('/api/v1/rules/evaluate', { records, tenant_id: tenantId }).then(r => r.data),
};

// ─── Transformation API ───────────────────────────────────────────────────────
export const transformApi = {
  transform: (records: Record<string, unknown>[], rules: Record<string, unknown>[]) =>
    transformClient.post('/api/v1/transform/transform', { records, rules }).then(r => r.data),

  listTransformationTypes: () =>
    transformClient.get('/api/v1/transform/transformations').then(r => r.data),
};

// ─── AI API ───────────────────────────────────────────────────────────────────
export const aiApi = {
  analyzeDocument: (text: string, documentType?: string) =>
    aiClient.post('/api/v1/ai/document/analyze', { text, document_type: documentType }).then(r => r.data),

  indexDocuments: (documents: string[], metadatas: Record<string, unknown>[], collectionName = 'platform_docs') =>
    aiClient.post('/api/v1/ai/rag/index', { documents, metadatas, collection_name: collectionName }).then(r => r.data),

  queryRAG: (question: string, collectionName = 'platform_docs') =>
    aiClient.post('/api/v1/ai/rag/query', { question, collection_name: collectionName }).then(r => r.data),

  detectAnomalies: (records: Record<string, unknown>[], numericFields: string[], detectFraud = false) =>
    aiClient.post('/api/v1/ai/anomaly/detect', { records, numeric_fields: numericFields, detect_fraud: detectFraud }).then(r => r.data),

  autoMap: (sourceFields: string[], targetSchema: Record<string, string>) =>
    aiClient.post('/api/v1/ai/mapping/auto', { source_fields: sourceFields, target_schema: targetSchema }).then(r => r.data),
};

// ─── Analytics API ────────────────────────────────────────────────────────────
export const analyticsApi = {
  getKPIs: (tenantId = 'default-tenant') =>
    analyticsClient.get('/api/v1/analytics/kpis', { params: { tenant_id: tenantId } }).then(r => r.data),

  getSummary: (tenantId = 'default-tenant', days = 7) =>
    analyticsClient.get('/api/v1/analytics/summary', { params: { tenant_id: tenantId, days } }).then(r => r.data),

  getQuality: (tenantId = 'default-tenant') =>
    analyticsClient.get('/api/v1/analytics/quality', { params: { tenant_id: tenantId } }).then(r => r.data),
};

// ─── Notification API ─────────────────────────────────────────────────────────
export const notificationApi = {
  send: (payload: Record<string, unknown>) =>
    notificationClient.post('/api/v1/notifications/send', payload).then(r => r.data),

  broadcast: (payload: Record<string, unknown>) =>
    notificationClient.post('/api/v1/notifications/broadcast', payload).then(r => r.data),

  getChannels: () =>
    notificationClient.get('/api/v1/notifications/channels').then(r => r.data),

  getHistory: (limit = 50) =>
    notificationClient.get('/api/v1/notifications/history', { params: { limit } }).then(r => r.data),

  getStats: () =>
    notificationClient.get('/api/v1/notifications/stats').then(r => r.data),
};
