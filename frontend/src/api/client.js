import axios from 'axios'

const http = axios.create({ baseURL: 'http://localhost:8000/api' })

export const startAnalysis = (request) => http.post('/analyze', request).then(r => r.data)
export const getJobStatus  = (jobId)   => http.get(`/analyze/${jobId}`).then(r => r.data)
export const getJobResults = (jobId)   => http.get(`/analyze/${jobId}/results`).then(r => r.data)
export const saveBaseline  = (request) => http.post('/baseline', request).then(r => r.data)
export const listReports   = ()        => http.get('/reports/list').then(r => r.data)
export const getPdfUrl      = (caseId) => `http://localhost:8000/api/reports/${caseId}/pdf`
export const getJsonUrl     = (caseId) => `http://localhost:8000/api/reports/${caseId}/json`
export const getHashesUrl   = (caseId) => `http://localhost:8000/api/reports/${caseId}/hashes`
export const getTimelineUrl = (caseId) => `http://localhost:8000/api/reports/${caseId}/timeline`
