import { defineConfig } from 'cypress';
import 'dotenv/config';
import { runAiAssert } from './cypress/support/ai/aiAssert';
import { runAiTriage } from './cypress/support/ai/aiTriage';
import { runAiGenerateTestCase } from './cypress/support/ai/aiGenerateTestCase';

export default defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || 'http://localhost:4173',
    supportFile: 'cypress/support/e2e.ts',
    setupNodeEvents(on) {
      // Architecture clé : les commandes IA sont de simples wrappers cy.task()
      // côté navigateur -> tout le code Node/LangChain tourne ici, jamais dans le browser.
      on('task', {
        aiAssert: runAiAssert,
        aiTriage: runAiTriage,
        aiGenerateTestCase: runAiGenerateTestCase,
        table(data) {
          console.table(data);
          return null;
        },
      });
    },
  },
});
