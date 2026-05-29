import { Request, Response, NextFunction } from 'express';
import { ZodType } from 'zod';
export declare const validate: (schema: ZodType<any>) => (req: Request, res: Response, next: NextFunction) => Promise<void>;
//# sourceMappingURL=event.middleware.d.ts.map