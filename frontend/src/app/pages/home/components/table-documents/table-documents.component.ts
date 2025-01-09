import { Component, ViewChild, OnInit } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { DocumentData } from '../../interface/documents.interface';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { DocumentService } from '../../services/documents-search.service';

@Component({
  selector: 'app-document-search',
  standalone: true,
  imports: [  
    MatFormFieldModule,
    MatInputModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatCheckboxModule ],
  templateUrl: './table-documents.component.html',
  styleUrls: ['./table-documents.component.css']
})
export class DocumentSearchComponent implements OnInit {
  // Definimos las columnas que queremos mostrar
  displayedColumns: string[] = ['id', 'name_document', 'full_content'];
  dataSource: MatTableDataSource<DocumentData>;
  isExactSearch: boolean = false;
  currentSearchTerm: string = '';
  isLoading: boolean = false;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(private documentService: DocumentService) {
    this.dataSource = new MatTableDataSource<DocumentData>([]);
  }
  

  ngOnInit() {
    // Realizamos la búsqueda inicial
    this.loadDocuments('');
  }

  // eslint-disable-next-line @angular-eslint/use-lifecycle-interface
  ngAfterViewInit() {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.currentSearchTerm = filterValue;
    this.loadDocuments(filterValue);
  }

  onExactSearchChange(event: any) {
    this.isExactSearch = event.checked;
    // Realizar nueva búsqueda con el término actual
    this.loadDocuments(this.currentSearchTerm);
  }
  handleSearchResults(results: any) {
    const documents = results.results.map((result: any) => ({
      _id: result.document_name,
      _source: {
        name_document: result.document_name,
        content: result.content, // Concatenar los highlights para formar el contenido
        page_number: result.page_number,
        total_pages: result.total_pages
      }
    }));
    this.dataSource.data = documents;
  }
  // eslint-disable-next-line @typescript-eslint/no-inferrable-types
  loadDocuments(searchTerm: string = ''): void {
    this.isLoading = true;
  
    // Elegir el método de búsqueda según el estado del checkbox
    const searchMethod = this.isExactSearch ? 
      this.documentService.exactSearchDocuments(searchTerm) :
      this.documentService.searchDocuments(searchTerm);
  
    // Suscribirse al método de búsqueda seleccionado
    searchMethod.subscribe({
      next: (response) => {
        console.log(response)
        // Mapear los resultados de la búsqueda a la estructura de DocumentData
        const documents = response.results.map((result: any) => ({
          _id: result.document_name,
          _source: {
            name_document: result.document_name,
            content: result.content, // Concatenar los highlights para formar el contenido
            page_number: result.page_number,
            total_pages: result.total_pages
          }
        }));
        // Asignar los documentos obtenidos al dataSource
        this.dataSource.data = documents;
      },
      error: (error) => {
        // Manejar errores en la carga de documentos
        console.error("Error al cargar documentos", error);
      },
      complete: () => {
        // Finalizar el estado de carga
        this.isLoading = false;
      }
    });
  }

}