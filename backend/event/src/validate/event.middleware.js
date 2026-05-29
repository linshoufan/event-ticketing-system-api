"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validate = void 0;
const zod_1 = require("zod");
const validate = (schema) => {
    return async (req, res, next) => {
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
        }
        catch (error) {
            if (error instanceof zod_1.ZodError) {
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
exports.validate = validate;
//# sourceMappingURL=event.middleware.js.map