import { Request, Response, NextFunction } from 'express';
import { ZodType, ZodError } from 'zod';

export const validate = (schema: ZodType<any>) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const validatedData = await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params,
      });

      req.body = validatedData.body;
      Object.assign(req.query, validatedData.query);
      Object.assign(req.params, validatedData.params);
      next();

    } catch (error) {
      if (error instanceof ZodError) {
        res.status(400).json({
          error: {
            code: 'BAD_REQUEST',
            message: '資料格式驗證錯誤',
            details: error.issues.map(e => ({ 
              path: e.path.join('.'), 
              message: e.message 
            }))
          }
        });
        return;
      }
      next(error);
    }
  };
};
