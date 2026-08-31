import type {
  DigitalHumanMode,
  DigitalHumanModesResponse,
  DigitalHumanResponse,
  DigitalHumanSpeakRequest,
  DigitalHumanState
} from '../types';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`);
  if (!response.ok) throw new Error(`Digital human request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(`Digital human request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export function createDigitalHumanSession(role: string, avatarId = 'medical_tutor_001') {
  return postJson<{ status: string; session_id: string; role: string; avatar_id: string; state: DigitalHumanState; mode: DigitalHumanMode }>(
    '/api/digital-human/session',
    { role, avatar_id: avatarId }
  );
}

export function getDigitalHumanModes() {
  return readJson<DigitalHumanModesResponse>('/api/digital-human/modes');
}

export function speakDigitalHuman(payload: DigitalHumanSpeakRequest) {
  return postJson<DigitalHumanResponse>('/api/digital-human/speak', payload);
}

export function updateDigitalHumanStatus(sessionId: string, state: DigitalHumanState, detail = '') {
  return postJson<{ status: string; session_id: string; state: DigitalHumanState }>(
    '/api/digital-human/status',
    { session_id: sessionId, state, detail }
  );
}

export function getMockDigitalHuman(state: DigitalHumanState) {
  return readJson<{ status: string; mode: 'mock'; state: DigitalHumanState; video_url: string | null; poster_url: string; provider: string }>(
    `/api/digital-human/mock-video?state=${encodeURIComponent(state)}`
  );
}

export function sendSparkOsAudio(audioBase64: string, uid = 'medical-student') {
  return postJson<{ status: string; text: string; audio_base64: string; audio_format: string }>(
    '/api/sparkos/audio-chat',
    { audio_base64: audioBase64, uid }
  );
}
