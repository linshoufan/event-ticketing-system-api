import { EventDB } from '../core/database'

describe('PostgreSQL Database Connection Test', () => {
  beforeAll(async () => {
    if (!EventDB.isInitialized) {
      await EventDB.initialize()
    }
  })

  afterAll(async () => {
    if (EventDB.isInitialized) {
      await EventDB.destroy()
    }
  })

  it('成功初始化 TypeORM EventDB', () => {
    expect(EventDB.isInitialized).toBe(true)
  })

  it('成功執行SQL查詢', async () => {
    const result = await EventDB.query('SELECT 1 AS result')
    expect(result).toBeDefined()
    expect(result[0].result).toBe(1)
  })

  it('確認連線的資料庫名稱是否正確', async () => {
    const result = await EventDB.query('SELECT current_database()')
    const dbName = result[0].current_database

    console.log(`目前連線的 PostgreSQL 資料庫: [${dbName}]`)
    expect(dbName).toStrictEqual('event_test_db')
    // expect(dbName).toStrictEqual('REAL NAME PLACEHOLDER')

  })
})
