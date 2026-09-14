# reelroom frontend

React + Vite film diary frontend for the existing FastAPI API.

1. Copy `.env.example` to `.env` and set `VITE_API_URL` (normally `http://localhost:8000`).
2. Run `npm install`.
3. Run `npm run dev`.

The client only uses the specified `/api` routes. It persists access and refresh tokens in local storage, refreshes after a 401, and clears the session if refresh fails.

## Original Vite notes

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
