import { Inject, Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { CookieService } from 'ngx-cookie-service';
import { BehaviorSubject, Observable, of, switchMap, catchError, forkJoin, map, filter, take, timeout } from 'rxjs';
import { NgxToolbarService, SessionState, OUContextModel, ModuleModel } from '@privally/ngx-toolbar';
import { SessionStatus } from './session-status.enum';
import { DomainService } from '@privally/ngx-toolbar';

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly statusSubject = new BehaviorSubject<SessionStatus>(SessionStatus.Initializing);
  readonly status$ = this.statusSubject.asObservable();

  private readonly stateSubject = new BehaviorSubject<SessionState | null>(null);
  readonly state$ = this.stateSubject.asObservable();

  private _initialized = false;

  get status(): SessionStatus { return this.statusSubject.value; }
  get state(): SessionState | null { return this.stateSubject.value; }
  get accessToken(): string | null { return this.toolbarService.loginResult?.accessToken ?? null; }

  constructor(
    @Inject('environment') private environment: any,
    private http: HttpClient,
    private cookieService: CookieService,
    private toolbarService: NgxToolbarService,
    private domainService: DomainService,
    private router: Router
  ) {}

  initialize(): Observable<SessionStatus> {
    if (this._initialized) return of(this.status);
    this._initialized = true;

    const refreshCookie = this.cookieService.get('x-refresh-token');
    if (!refreshCookie) {
      this.setStatus(SessionStatus.Unauthenticated);
      return of(SessionStatus.Unauthenticated);
    }

    let refreshTokenValue: any;
    try {
      refreshTokenValue = JSON.parse(refreshCookie);
    } catch {
      this.clearSessionData();
      this.setStatus(SessionStatus.Unauthenticated);
      return of(SessionStatus.Unauthenticated);
    }

    if (!refreshTokenValue?.tokenHash) {
      this.clearSessionData();
      this.setStatus(SessionStatus.Unauthenticated);
      return of(SessionStatus.Unauthenticated);
    }

    return this.toolbarService.antiforgery().pipe(
      switchMap(() => this.toolbarService.refreshToken()),
      switchMap((success: Boolean) => {
        if (!success) {
          return of(null as { contexts: OUContextModel[]; meta: SessionState } | null);
        }
        return forkJoin({
          contexts: this.toolbarService.getContexts(),
          meta: this.http.get<SessionState>(
            `https://apigw.${this.domainService.getCurrentDomain()}${this.environment.api.sso}/api/v2/users/getMetaSession`,
            this.getHeaders()
          ),
        }).pipe(
          catchError(() => of(null as { contexts: OUContextModel[]; meta: SessionState } | null))
        );
      }),
      map((result) => {
        if (!result || !result.meta) {
          this.setStatus(SessionStatus.Unauthenticated);
          return SessionStatus.Unauthenticated;
        }
        const { contexts, meta } = result;
        if (contexts?.length <= 0) {
          this.setStatus(SessionStatus.Unauthenticated);
          return SessionStatus.Unauthenticated;
        }
        meta.contexts = contexts;
        meta.context = this.getLastContext(contexts);
        if (!meta.context && contexts?.length > 0) {
          meta.context = contexts[0];
        }
        this.stateSubject.next(meta);
        this.setStatus(SessionStatus.Authenticated);
        return SessionStatus.Authenticated;
      }),
      catchError((err) => {
        console.error('[SSO-F01]', err);
        this.clearSessionData();
        this.setStatus(SessionStatus.Unauthenticated);
        return of(SessionStatus.Unauthenticated);
      })
    );
  }

  actionsFor(moduleCode: string): string[] {
    const state = this.state;
    if (!state?.modules) return [];
    const mod = state.modules.find((m: ModuleModel) => m.module === moduleCode);
    return mod?.actions ?? [];
  }

  findModule(moduleCode: string): ModuleModel | undefined {
    const state = this.state;
    if (!state?.modules) return undefined;
    return state.modules.find((m: ModuleModel) => m.module === moduleCode);
  }

  redirectToLogin(target?: { module: string; path: string }): void {
    if (target) {
      const domain = `.${this.domainService.getCurrentDomain()}`;
      this.cookieService.set(
        'x-post-login-target',
        JSON.stringify(target),
        { expires: new Date(Date.now() + 10 * 60_000), domain, secure: true, sameSite: 'Strict', path: '/' }
      );
    }
    this.clearSessionData();
    const sso = this.cookieService.get('x-url-sso') || `https://${window.location.hostname}`;
    window.location.href = sso;
  }

  private setStatus(status: SessionStatus): void { this.statusSubject.next(status); }

  private clearSessionData(): void {
    sessionStorage.clear();
    localStorage.clear();
    this.cookieService.delete('x-url-redirect', '/', `.${this.domainService.getCurrentDomain()}`, true, 'Strict');
    this.cookieService.delete('x-refresh-token', '/', `.${this.domainService.getCurrentDomain()}`, true, 'Strict');
  }

  private getLastContext(contexts: OUContextModel[]): OUContextModel | undefined {
    const lastId = Number(sessionStorage.getItem('Suite-Owner'));
    if (!lastId) return undefined;
    return contexts.find((c) => c.id === lastId);
  }

  private getHeaders() {
    return {
      headers: new HttpHeaders({
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.toolbarService.loginResult?.accessToken ?? ''}`,
        'X-XSRF-TOKEN': this.cookieService.get('XSRF-TOKEN'),
        'x-api-key': this.environment.xApiKey,
      }),
      withCredentials: true,
    };
  }
}
