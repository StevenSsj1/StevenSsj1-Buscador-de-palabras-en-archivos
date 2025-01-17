import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../../../environments/enviroment';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private baseUrl = environment.apiUrl;
  private documentCount = new BehaviorSubject<number>(0);
  documentCount$ = this.documentCount.asObservable();

  constructor(private http: HttpClient) {}

  searchDocuments(searchTerm: string = ''): Observable<any> {
    return this.http.get(
      `${this.baseUrl}/api_documents/search/`,
      { params: { search_term: searchTerm } }
    ).pipe(
      tap((response: any) => this.updateCount(response.results.length)) // Asegúrate de que response.totalCount es el valor correcto
    );
  }

  exactSearchDocuments(searchTerm: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/api_documents/search_exact?search_term=${searchTerm}&index_name=pdfs&size=100`)
      .pipe(
        tap((response: any) => this.updateCount(response.totalCount)) // Asegúrate de que response.totalCount es el valor correcto
      );
  }

  checkNewFiles(): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/api_documents/check_new_files`, {});
  }

  updateCount(count: number) {
    this.documentCount.next(count);
  }

  resetCount() {
    this.documentCount.next(0);
  }
}