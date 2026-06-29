import 'dotenv/config';
import { ChatAnthropic } from '@langchain/anthropic';
import { ChatOpenAI } from '@langchain/openai';

// Client LLM unique, partagé par toutes les commandes IA.
// LangSmith trace automatiquement chaque appel dès que les variables
// LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY / LANGCHAIN_PROJECT sont
// présentes en env — aucun code de tracing à écrire ici (zero-instrumentation).
export function getChatModel(temperature = 0) {
  const provider = process.env.AI_PROVIDER || 'anthropic';

  if (provider === 'openai') {
    return new ChatOpenAI({
      model: process.env.AI_MODEL || 'gpt-4o-mini',
      temperature,
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  return new ChatAnthropic({
    model: process.env.AI_MODEL || 'claude-sonnet-4-6',
    temperature,
    apiKey: process.env.ANTHROPIC_API_KEY,
  });
}
