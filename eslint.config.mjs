import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextVitals,
  ...nextTs,
  {
    ignores: [
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
      "node_modules/**",
      ".cache/**",
      ".remember/**",
      ".electron/**",
      "dist/**",
      "public/**",
    ],
  },
  {
    rules: {
      // This app renders arbitrary local image files via <img src="/api/image">,
      // which next/image cannot optimize — <img> is the correct element here.
      "@next/next/no-img-element": "off",
    },
  },
];

export default eslintConfig;
