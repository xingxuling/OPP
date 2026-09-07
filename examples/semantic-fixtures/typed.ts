export function normalizeUser(username: string, age: number): boolean {
  return age >= 0 && username.length > 0;
}
