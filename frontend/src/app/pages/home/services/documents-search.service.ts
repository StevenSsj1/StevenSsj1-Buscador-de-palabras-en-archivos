import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { environment } from "../../../../environments/enviroment";

@Injectable({
    providedIn: 'root'
})
export class DocumentService{
    private baseUrl = environment.apiUrl;

    constructor(private http: HttpClient){}

    // eslint-disable-next-line @typescript-eslint/no-inferrable-types, @typescript-eslint/no-explicit-any
    searchDocuments(searchTerm: string = ''): Observable<any>{
        return this.http.get(
            `${this.baseUrl}/api_documents/search/`,
            { params : { search_term: searchTerm}}
        )
    }
  
    exactSearchDocuments(searchTerm: string): Observable<any>{
      return this.http.get(`${this.baseUrl}/api_documents/exact_search?search_term=${searchTerm}&index_name=pdfs&size=100`);
    }

}