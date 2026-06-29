import { z } from 'zod';
import { getChatModel } from './langchainClient';

const ResultSchema = z.object({
  pass: z.boolean().describe('true si l\'intention décrite est satisfaite par la page'),
  reason: z.string().describe('justification courte, basée sur des éléments observés dans le DOM'),
});

interface AiAssertInput {
  html: string;
  intent: string;
  url: string;
}

export async function runAiAssert({ html, intent, url }: AiAssertInput) {
  const model = getChatModel(0).withStructuredOutput(ResultSchema, { name: 'ai_assert_result' });

  const result = await model.invoke([
    [
      'system',
      'Tu es un agent de QA. On te donne le HTML brut d\'une page web et une ' +
      'intention fonctionnelle à vérifier. Réponds uniquement à partir de ce ' +
      'que tu observes dans le HTML fourni, jamais en supposant.',
    ],
    [
      'human',
      `URL courante: ${url}\n\nIntention à vérifier: "${intent}"\n\nHTML (tronqué):\n${html}`,
    ],
  ]);

  return result; // { pass, reason } — validé par le schéma Zod
}
