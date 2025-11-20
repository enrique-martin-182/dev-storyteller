import { http, HttpResponse, ws } from 'msw';

const API_BASE_URL = '';

export const handlers = [
  // Mock for GET /api/v1/repositories/
  http.get(`${API_BASE_URL}/api/v1/repositories/`, () => {
    console.log('Intercepted GET /api/v1/repositories/');
    return HttpResponse.json([
      { id: 1, name: 'mock-repo-1', url: 'http://github.com/mock/repo-1', status: 'completed' },
      { id: 2, name: 'mock-repo-2', url: 'http://github.com/mock/repo-2', status: 'pending' },
    ]);
  }),

  // Mock for GET /api/v1/repositories/:repoId/analysis
  http.get(`${API_BASE_URL}/api/v1/repositories/:repoId/analysis`, ({ params }) => {
    const { repoId } = params;
    if (repoId === '1') {
      return HttpResponse.json([
        {
          id: 1,
          summary: 'Mock analysis summary for repo 1',
          file_count: 100,
          commit_count: 50,
          languages: { 'JavaScript': 10, 'HTML': 5 },
          created_at: new Date().toISOString(),
        },
      ]);
    }
    return HttpResponse.json([]);
  }),

  // Mock for POST /api/v1/repositories/
  http.post(`${API_BASE_URL}/api/v1/repositories/`, async ({ request }) => {
    const newRepo = await request.json();
    return HttpResponse.json(
      {
        id: 3,
        name: newRepo.url.split('/').pop(),
        url: newRepo.url,
        status: 'pending',
      },
      { status: 200 }
    );
  }),

  // Mock for WebSocket connections
  ws.link(`${API_BASE_URL}/api/v1/ws/status`, (server) => {
    server.on('connection', (client) => {
      client.send(JSON.stringify({ id: 1, status: 'completed' }));
    });
  }),
];
