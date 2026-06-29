import { z } from 'zod';
import { getChatModel } from './langchainClient';

const TriageSchema = z.object({
  category: z.enum(['real_bug', 'flaky', 'environment_issue']),
  confidence: z.number().min(0).max(1),
  reasoning: z.string(),
});

interface AiTriageInput {
  testTitle: string;
  errorMessage: string;
  html: string;
}

export async function runAiTriage({ testTitle, errorMessage, html }: AiTriageInput) {
  const model = getChatModel(0).withStructuredOutput(TriageSchema, { name: 'ai_triage_result' });

  return model.invoke([
    [
      'system',
      'Tu es un agent de triage QA. Classe l\'échec d\'un test E2E selon trois ' +
      'catégories: real_bug (régression probable), flaky (instabilité de timing/réseau), ' +
      'environment_issue (problème d\'environnement/data, pas un bug applicatif). ' +
      'Sois prudent: en cas de doute, baisse la confiance plutôt que de trancher au hasard.',
    ],
    [
      'human',
      `Test: "${testTitle}"\nErreur Cypress: ${errorMessage}\n\nÉtat du DOM au moment de l'échec (tronqué):\n${html}`,
    ],
  ]);
}
