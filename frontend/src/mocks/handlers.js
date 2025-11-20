import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const handlers = [
  // Mock for GET /api/v1/repositories/
  http.get(`${API_BASE_URL}/repositories/`, () => {
    return HttpResponse.json([
      { id: 1, name: 'mock-repo-1', url: 'http://github.com/mock/repo-1', status: 'completed' },
      { id: 2, name: 'mock-repo-2', url: 'http://github.com/mock/repo-2', status: 'pending' },
    ]);
  }),

  // Mock for GET /api/v1/repositories/:repoId/analysis
  http.get(`${API_BASE_URL}/repositories/:repoId/analysis`, ({ params }) => {
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
  http.post(`${API_BASE_URL}/repositories/`, async ({ request }) => {
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
];
