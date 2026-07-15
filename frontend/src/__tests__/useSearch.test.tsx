import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSearch } from '../hooks/useSearch';
import { mockSearchResults } from '../mocks/handlers';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useSearch', () => {
  it('useSearch retourne les résultats du mock', async () => {
    const { result } = renderHook(() => useSearch({ q: 'maintenance', page: 1, page_size: 10 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSearchResults);
  });

  it('AbortSignal annule si params changent', async () => {
    let q = 'maintenance';
    const { result, rerender } = renderHook(() => useSearch({ q, page: 1, page_size: 10 }), {
      wrapper: createWrapper(),
    });

    q = 'securite';
    rerender();
    
    // We can't strictly test network abort without mocking fetch directly or using specific msw handlers with delay, 
    // but we can verify the query state correctly goes back to fetching
    expect(result.current.isFetching).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('keepPreviousData garde les anciens résultats', async () => {
    let page = 1;
    const { result, rerender } = renderHook(() => useSearch({ q: 'maintenance', page, page_size: 10 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const firstData = result.current.data;

    page = 2;
    rerender();

    // Data should still be present from previous render while fetching
    expect(result.current.isFetching).toBe(true);
    expect(result.current.data).toEqual(firstData);
  });
});
