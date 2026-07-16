import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, ".", "");

  return {
    plugins: [react()],
    define: {
      // Make VITE_ prefixed env vars available
      "import.meta.env.VITE_BACKEND_HOST_URL": JSON.stringify(
        env.VITE_BACKEND_HOST_URL || ""
      ),
    },
    server: {
      // Disable HTTPS for local development
      https: false,
      // Proxy /media requests to Django backend
      proxy: {
        '/media': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
