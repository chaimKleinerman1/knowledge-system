import { AppProviders } from '@/app/providers/AppProviders';
import { HomePage } from '@/pages/home/HomePage';

export const App = () => (
  <AppProviders>
    <HomePage />
  </AppProviders>
);
