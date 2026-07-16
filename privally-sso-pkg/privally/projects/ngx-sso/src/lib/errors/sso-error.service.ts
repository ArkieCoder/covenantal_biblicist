import { Injectable } from '@angular/core';

export type SsoErrorCode =
  | 'SSO-F01'
  | 'SSO-F02'
  | 'SSO-F03'
  | 'SSO-F04'
  | 'SSO-F05'
  | 'SSO-F06'
  | 'SSO-F07';

@Injectable({ providedIn: 'root' })
export class SsoErrorService {
  report(code: SsoErrorCode, detail?: unknown): void {
    console.error(`[${code}]`, detail ?? '');
  }
}
