import request from 'supertest'
import app from '../app'
import { EventDB } from '../core/database'
import { EventEntity, EventIdPool } from '../model/event.model'
import { EventStatus } from '../interface/event.interface'
import { generateToken, UserRole } from '../middleware/auth.middleware'

// Test Case 1
const PartyEventMock = {
  name: "International Kaohsiung Picnic Festival 2038",
  description: "A joyful and memorable event that attracts people of all ages around Taiwan.",
  location: "Kaohsiung City",
  category: "Recreation",
  guestAllowed: true,
  ticketLimit: 50000,
  remainingTickets: 47500,
  registrationStart: new Date(Date.now() + 86400000 * 5),
  registrationEnd: new Date(Date.now() + 86400000 * 10),
  eventStartTime: new Date(Date.now() + 86400000 * 15),
  eventEndTime: new Date(Date.now() + 86400000 * 17),
  cancellationDeadline: new Date(Date.now() + 86400000 * 12),
  status: EventStatus.NOT_OPEN,
  isDraft: false,
  latitude: 22.62987218107962,
  longitude: 120.30292453700281,
  checkinRadiusMeters: 1000,
  faqs: [
    { question: "Is parking available?", answer: "Yes, underground parking is provided." },
    { question: "Are meals included?", answer: "This is picnic. Bring your own food! :)" }
  ]
}

// Test Case 2
const MusicEventMock = {
  name: "Summer Sonic Hsinchu 2050",
  description: "The biggest outdoor electronic music festival in Hsinchu featuring international renowned band Coldplay!!",
  location: "Hsinchu City",
  category: "Music",
  guestAllowed: false,
  ticketLimit: 5000,
  remainingTickets: 1900,
  registrationStart: new Date(Date.now() + 86400000 * 1),
  registrationEnd: new Date(Date.now() + 86400000 * 25),
  eventStartTime: new Date(Date.now() + 86400000 * 30),
  eventEndTime: new Date(Date.now() + 86400000 * 32),
  cancellationDeadline: new Date(Date.now() + 86400000 * 20),
  status: EventStatus.REGISTERING,
  isDraft: true,
  latitude: 24.8211,
  longitude: 121.0182,
  checkinRadiusMeters: 500,
  faqs: [
    { question: "Can I bring outside food?", answer: "Yes, but please clean up before leaving." }
  ]
}

const dummyUser1 = generateToken({
  userId: 'dummy001',
  email: 'example_welfare@mail.com',
  role: UserRole.WELFARE_MEMBER
})

const dummyUser2 = generateToken({
  userId: 'dummy002',
  email: 'example_user@mail.com',
  role: UserRole.USER
})


describe('Event Integration Tests', () => {
  const Repo = EventDB.getRepository(EventEntity)
  const IdRepo = EventDB.getRepository(EventIdPool)

  beforeAll(async () => {
    await EventDB.initialize()
    await EventDB.synchronize(true)
  })

  afterAll(async () => {
    await EventDB.destroy()
  })

  beforeEach(async () => {
      await request(app).post('/v1/events').set('Authorization', `Bearer ${dummyUser1}`).send(PartyEventMock)
      await request(app).post('/v1/events').set('Authorization', `Bearer ${dummyUser1}`).send(MusicEventMock)
    })

  afterEach(async () => {
    await Repo.clear()
    await IdRepo.clear()
  })


  describe('Event ID Pool Logic: GET, POST and DELETE /v1/events/:event_id', () => {
    it('新增多個活動後查看所有活動，嘗試刪除報名中活動會失敗', async () => {
      const faq1 = [
        { question: "Is parking available?", answer: "Yes, underground parking is provided." },
        { question: "Are meals included?", answer: "This is picnic. Bring your own food! :)" }
      ]
      const faq2 = [{ question: "Can I bring outside food?", answer: "Yes, but please clean up before leaving." }]

      const response1 = await request(app)
      .get('/v1/events/event_1')
      .set('Authorization', `Bearer ${dummyUser2}`)

      expect(response1.status).toBe(200)
      expect(response1.body.data.eventId).toBe('event_1')
      expect(response1.body.data).toHaveProperty('name')
      expect(response1.body.data.faqs).toEqual(faq1)

      const response2 = await request(app)
      .get('/v1/events/event_2')
      .set('Authorization', `Bearer ${dummyUser2}`)

      expect(response1.status).toBe(200)
      expect(response2.body.data.eventId).toBe('event_2')
      expect(response2.body.data).toHaveProperty('category')
      expect(response2.body.data.faqs).toEqual(faq2)

      const response3 = await request(app).delete('/v1/events/event_2').set('Authorization', `Bearer ${dummyUser1}`)
      expect(response3.status).toBe(409)
    })
  })

  describe('Batch Update Events Logic: PUT /v1/events', () => {
    it('批量更新活動，同時回傳成功與失敗的活動ID', async () => {
      const updates = {
        updates: [
          { eventId: 'event_1', name: 'Beer Harvesting Ceremony 2029' },
          { eventId: 'event_100', name: 'Ghost Event' }
        ]
      }

      // 測試：一般 user 無法更改活動
      const invalidResp = await request(app)
      .patch('/v1/events')
      .set('Authorization', `Bearer ${dummyUser2}`)
      .send(updates)

      expect(invalidResp.status).toBe(403)

      const resp = await request(app)
      .patch('/v1/events')
      .set('Authorization', `Bearer ${dummyUser1}`)
      .send(updates)

      // console.log(resp.text)
      expect(resp.status).toBe(207)
      expect(resp.body.data.succeeded).toContain('event_1')
      expect(resp.body.data.failed).toStrictEqual(
        [{ eventId: 'event_100', error: 'EVENT_NOT_FOUND' }]
      )
    })
  })

  describe('Check Event List: POST and GET /v1/events/', () => {
    beforeEach(async () => {
      await Repo.clear()
      await IdRepo.clear()

      await request(app).post('/v1/events').set('Authorization', `Bearer ${dummyUser1}`)
      .send({
        name: "Traditional Food Festival",
        description:"Come to Hsinchu and enjoy nothing but the very expensive food!",
        location: 'Tainan',
        category: "Food & Travel",
        remainingTickets: 2500,
        registrationStart: new Date(),
        registrationEnd: new Date(Date.now() + 86400000 * 10),
        eventStartTime: new Date(Date.now() + 86400000 * 20),
        eventEndTime: new Date(Date.now() + 86400000 * 25),
        status: EventStatus.REGISTERING
      })
      await request(app).post('/v1/events').set('Authorization', `Bearer ${dummyUser1}`)
      .send({
        name: "Non-international Music Festival",
        description: "Pop, Rock, and Rap music performed by domestic singers.",
        location: 'Hsinchu',
        category: "Music & Recreation",
        remainingTickets: 3000,
        registrationStart: new Date(),
        registrationEnd: new Date(Date.now() + 86400000 * 10),
        eventStartTime: new Date(Date.now() + 86400000 * 20),
        eventEndTime: new Date(Date.now() + 86400000 * 25),
        status: EventStatus.REGISTERING
      })
      await request(app).post('/v1/events').set('Authorization', `Bearer ${dummyUser1}`)
      .send({
        name: "Ancient Artifact Exhibition",
        description: "Really ancient artworks. Come and see the potential beauty within them.",
        location: 'Taipei',
        category: "Art & Life",
        remainingTickets: 1000,
        registrationStart: new Date(),
        registrationEnd: new Date(Date.now() + 86400000 * 10),
        eventStartTime: new Date(Date.now() + 86400000 * 20),
        eventEndTime: new Date(Date.now() + 86400000 * 25),
        status: EventStatus.ENDED
      })
    })

    it('查詢結果應預設排除已結束活動', async () => {
      const resp = await request(app)
      .get('/v1/events')
      .set('Authorization', `Bearer ${dummyUser2}`)
      .send({ page: 1, limit: 3 })

      // console.log(resp.text)
      expect(resp.body.pagination.total).toBe(2)
      expect(resp.body.data.length).toBe(2)

      // Validate 去蕪存菁 logic
      resp.body.data.forEach((event: any) => {
        expect(event.eventId).toBeDefined()
        expect(event.name).toBeDefined()
        expect(event.location).toBeDefined()

        expect(event.latitude).toBeUndefined()
        expect(event.longitude).toBeUndefined()
        expect(event.checkinRadiusMeters).toBeUndefined()
        expect(event.faqs).toBeUndefined()
        expect(event.isDraft).toBeUndefined()
        expect(event.createdAt).toBeUndefined()
      })
    })

    it('活動查詢：不區分大小寫關鍵字搜尋 (ILIKE)', async () => {
      // Searching for "node" should match "Node.js Workshop"
      const resp = await request(app)
      .get('/v1/events')
      .set('Authorization', `Bearer ${dummyUser2}`)
      .send({ page: 1, limit: 1, filters: { keyword: 'food' } })

      // console.log(resp.text)
      expect(resp.status).toBe(200)
      expect(resp.body.pagination.total).toBe(1)
      expect(resp.body.data.length).toBe(1)
      expect(resp.body.data[0].name).toEqual('Traditional Food Festival')
    })

    it('活動查詢結果應正確反應欲搜尋的類型和狀態', async () => {
      // Filter by category "Music"
      const resp = await request(app)
      .get('/v1/events')
      .set('Authorization', `Bearer ${dummyUser2}`)
      .send({ page: 1, limit: 2, filters: { status: EventStatus.REGISTERING } })

      // console.log(resp.text)
      expect(resp.status).toBe(200)
      expect(resp.body.pagination.total).toBe(2)
      expect(resp.body.data.length).toBe(2)
    })

    it('活動列表不同分頁顯示的活動不應重疊', async () => {
      const resp1 = await request(app)
      .get('/v1/events')
      .set('Authorization', `Bearer ${dummyUser2}`)
      .send({ page: 1, limit: 1 })

      expect(resp1.status).toBe(200)
      expect(resp1.body.pagination.total).toBe(2)
      expect(resp1.body.data.length).toBe(1)

      const resp2 = await request(app)
      .get('/v1/events')
      .set('Authorization', `Bearer ${dummyUser2}`)
      .send({ page: 2, limit: 1 })

      expect(resp2.status).toBe(200)
      expect(resp2.body.pagination.total).toBe(2)
      expect(resp2.body.data.length).toBe(1)

      expect(resp1.body.data[0].name).not.toBe(resp2.body.data[0].name)
    })
  })
})
