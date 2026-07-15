import { http, HttpResponse } from 'msw';

export const mockSearchResults = {
  total: 2,
  page: 1,
  page_size: 10,
  query: 'maintenance',
  results: [
    {
      id: '1',
      title: 'Guide de Maintenance',
      content_preview: 'Ce guide couvre la maintenance de la ligne A.',
      file_type: 'pdf',
      tags: ['maintenance', 'ligne-a'],
      score: 0.95,
      thumbnail_url: 'http://example.com/doc1.pdf'
    },
    {
      id: '2',
      title: 'Rapport de sécurité',
      content_preview: 'Rapport de sécurité hebdomadaire.',
      file_type: 'docx',
      tags: ['sécurité'],
      score: 0.85,
      thumbnail_url: 'http://example.com/doc2.docx'
    }
  ]
};

export const handlers = [
  http.get('http://localhost:8000/api/search/', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q');
    
    if (q === 'empty') {
      return HttpResponse.json({ total: 0, page: 1, page_size: 10, results: [] });
    }
    
    return HttpResponse.json(mockSearchResults);
  }),

  http.post('http://localhost:8000/api/search/chat/', () => {
    return HttpResponse.json({
      answer: "Voici une réponse générée par l'IA.",
      sources: [
        { document_id: "1", text: "extrait pertinent", score: 0.9 }
      ]
    });
  }),

  http.post('http://localhost:8000/api/auth/login/', () => {
    return HttpResponse.json({
      access: 'fake-access-token',
      refresh: 'fake-refresh-token',
      user: {
        id: 1,
        username: 'operator',
        email: 'operator@example.com',
        role: 'operator',
        is_admin: false
      }
    });
  }),

  http.get('http://localhost:8000/api/auth/me/', () => {
    return HttpResponse.json({
      id: 1,
      username: 'operator',
      email: 'operator@example.com',
      role: 'operator',
      is_admin: false
    });
  })
];
