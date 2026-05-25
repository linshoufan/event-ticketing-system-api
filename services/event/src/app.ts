import express from 'express';
import cors from 'cors';
import eventRouter from './route/event.route';

const app = express();
app.use(cors());
app.use(express.json());
app.use('/v1/events', eventRouter);

export default app;
