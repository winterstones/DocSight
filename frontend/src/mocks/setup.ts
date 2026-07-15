import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './server';
import { cleanup } from '@testing-library/react';


beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
  window.HTMLElement.prototype.scrollIntoView = function() {};
});
afterEach(() => {
  server.resetHandlers();
  cleanup();
});
afterAll(() => server.close());
