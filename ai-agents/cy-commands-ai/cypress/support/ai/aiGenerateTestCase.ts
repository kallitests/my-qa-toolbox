import { z } from 'zod';
import { getChatModel } from './langchainClient';

const TestCaseSchema = z.object({
  id: z.string(),
  title: z.string(),
  preconditions: z.string(),
  steps: z.array(z.string()),
  expected: z.string(),
});

const OutputSchema = z.object({
  testCases: z.array(TestCaseSchema),
});

interface AiGenerateInput {
  userStory: string;
}

export async function runAiGenerateTestCase({ userStory }: AiGenerateInput) {
  const model = getChatModel(0.2).withStructuredOutput(OutputSchema, { name: 'test_case_generation' });

  return model.invoke([
    [
      'system',
      'Tu es un SDET senior. À partir d\'une user story en langage naturel, ' +
      'génère une liste de cas de test (cas nominal + au moins un cas limite/négatif). ' +
      'Chaque id suit le format TCxx. Sois concret et actionnable, pas générique.',
    ],
    ['human', userStory],
  ]);
}
