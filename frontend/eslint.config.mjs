import js from '@eslint/js';
import prettierRecommended from 'eslint-plugin-prettier/recommended';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist/**', 'coverage/**', 'node_modules/**'] },
  // A disable comment that suppresses nothing misleads the next reader, so a stale one fails lint.
  { linterOptions: { reportUnusedDisableDirectives: 'error' } },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, react.configs.flat.recommended],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: { ...globals.browser, ...globals.node, ...globals.es2022 },
    },
    plugins: { 'react-hooks': reactHooks, 'simple-import-sort': simpleImportSort },
    // Pinned rather than 'detect': the plugin's auto-detection calls an API that ESLint 10 removed.
    settings: { react: { version: '19.3' } },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',

      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',

      'object-curly-spacing': ['warn', 'always'],
      'no-unused-vars': 'off',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-redeclare': 'off',

      'react/jsx-key': 'error',
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react/no-unescaped-entities': 'off',

      // Deep paths are private to antd and move between majors.
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['antd/lib/**', 'antd/es/**'],
              message: "Import from 'antd'. Deep paths are private and move between majors.",
            },
            {
              group: ['rc-*/lib/**', 'rc-*/es/**', '@rc-component/*/lib/**', '@rc-component/*/es/**'],
              message: 'rc-* packages are antd internals. Derive the type from the public antd props instead.',
            },
            {
              group: ['@ant-design/icons/lib/**', '@ant-design/icons/es/**'],
              message: "Import from '@ant-design/icons'.",
            },
          ],
        },
      ],
    },
  },
  // Type-aware rules, scoped to `src` because only that folder belongs to tsconfig.json.
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { '@typescript-eslint': tseslint.plugin },
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      // `void promise` is the marker for a deliberate fire-and-forget.
      '@typescript-eslint/no-floating-promises': 'error',
    },
  },
  // Must stay last so it wins the formatting-related rules.
  prettierRecommended,
);
