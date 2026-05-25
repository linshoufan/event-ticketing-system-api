/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',

  testMatch: ['<rootDir>/src/test/*test.ts'],
  verbose: true,
  forceExit: true,
  clearMocks: true,
  setupFiles: ["dotenv/config"]
};
