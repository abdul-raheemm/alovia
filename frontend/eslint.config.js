import js from '@eslint/js'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import reactHooks from 'eslint-plugin-react-hooks'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  {
    ignores: [
      '**/node_modules',
      '**/dist',
      '**/dev-dist',
      'packages/shared/src/api-types.ts',
      'apps/patient-web/src/app/symptomBundle.generated.ts',
      'playwright-report',
      'test-results',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.strict,
  jsxA11y.flatConfigs.recommended,
  reactHooks.configs.flat['recommended-latest'],
  {
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    // CODE_STYLE.md §9: no console.log in committed code; errors go through reportError
    rules: { 'no-console': 'error' },
  },
  // build tooling (not app code) may print progress
  { files: ['scripts/**'], rules: { 'no-console': 'off' } },
)
