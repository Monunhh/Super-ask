import { defineConfig } from "vitest/config";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths()],
  test: {
    root: process.cwd(),
    environment: "node",
    include: ["Demo1/3_integration_testing/**/*.integration.test.ts"],
  },
});