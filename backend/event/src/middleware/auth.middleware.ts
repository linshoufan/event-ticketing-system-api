import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'dev_secret_change_in_production';

// 角色類型
export enum UserRole {
  ADMIN          = 'admin',
  WELFARE_MEMBER = 'welfare_member',
  USER           = 'user'
}

// 角色權限
export const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  [UserRole.ADMIN]:          ['create', 'read', 'update', 'delete', 'batch_create', 'batch_read', 'batch_delete'],
  [UserRole.WELFARE_MEMBER]: ['create', 'read', 'update', 'delete', 'batch_create', 'batch_read', 'batch_delete'],
  [UserRole.USER]:           ['read', 'batch_read'],
};

// Custom JWT Payload
export interface JwtPayload {
  userId: string;
  email: string;
  role: UserRole;
}

// 擴充 Express Request，後續可存取 req.user
declare global {
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

/**
 * 從 Authorization: Bearer <token> header 解析並驗證 JWT
 * 驗證成功後將 payload 掛載至 req.user
 */
export const requireAuth = (req: Request, res: Response, next: NextFunction): void => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({
      error: { code: 'UNAUTHORIZED', message: 'Missing or Invalid Authorization Header' }
    });
    return;
  }

  const token = authHeader.split(' ')[1];
  try {
    if (token != null) {
      const payload = jwt.verify(token, JWT_SECRET) as unknown as JwtPayload;
      req.user = payload;
      next();
    }
  } catch (err) {
    if (err instanceof jwt.TokenExpiredError) {
      res.status(401).json({ error: { code: 'TOKEN_EXPIRED', message: 'Token已過期' } });
    } else {
      res.status(401).json({ error: { code: 'INVALID_TOKEN', message: '無效Token' } });
    }
  }
};

/**
 * 必須在 requireAuth 之後驗證
 * 檢查 req.user.role 是否在允許的角色清單中
 *
 * @example
 * router.delete('/:eventId', requireAuth, requireRole([UserRole.ADMIN, UserRole.WELFARE_MEMBER]), handler)
 */
export const requireRole = (allowedRoles: UserRole[]) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: { code: 'USER_UNAUTHORIZED', message: '使用者未授權' } });
      return;
    }

    if (!allowedRoles.includes(req.user.role)) {
      res.status(403).json({
        error: {
          code: 'USER_FORBIDDEN',
          message: `當前角色權限不足進行此操作 (身分：${req.user.role})`
        }
      });
      return;
    }
    next();
  };
};

/**
 * generateToken(payload, expiresIn?)
 * 僅供開發和測試使用，生產環境應由獨立 Auth Service 發放
 */
export const generateToken = (payload: JwtPayload, expiresIn: string = '8h'): string => {
  return jwt.sign(payload, JWT_SECRET, { expiresIn } as jwt.SignOptions);
};
