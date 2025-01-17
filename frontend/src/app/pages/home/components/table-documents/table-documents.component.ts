import { Component, ViewChild, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
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
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { NgIf } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { FileDetectionDialogComponent } from './document-search.component';
import { LoggingService } from '../../../../service/logging.service';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';

@Component({
  selector: 'app-document-search',
  standalone: true,
  imports: [ 
    MatProgressSpinnerModule,
    MatButtonModule, 
    MatFormFieldModule,
    MatInputModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatCheckboxModule,
    ReactiveFormsModule,
    NgIf ], 
  templateUrl: './table-documents.component.html',
  styleUrls: ['./table-documents.component.css']
})
export class DocumentSearchComponent implements OnInit, AfterViewInit, OnDestroy {
  displayedColumns: string[] = ['id', 'name_document', 'full_content', 'page_number', 'relative_path'];
  dataSource: MatTableDataSource<DocumentData>;
  isExactSearch: boolean = false;
  currentSearchTerm: string = '';
  isLoading: boolean = false;
  isCheckingNewFiles: boolean = false;
  searchControl = new FormControl(''); // Add this
  private destroy$ = new Subject<void>(); // Add this for cleanup


  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private documentService: DocumentService, 
    private dialog: MatDialog,
    private logger: LoggingService,

  ) {
    this.dataSource = new MatTableDataSource<DocumentData>([]);
  }

  ngOnInit() {
    // Setup the debounced search
    this.searchControl.valueChanges.pipe(
      debounceTime(500), // Wait 500ms after the user stops typing
      distinctUntilChanged(), // Only emit if the value has changed
      takeUntil(this.destroy$)
    ).subscribe(value => {
      this.currentSearchTerm = value || '';
      this.loadDocuments(this.currentSearchTerm);
    });

    // Initial load
    this.loadDocuments('');
  }
  ngAfterViewInit() {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.searchControl.setValue(filterValue);
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
  onExactSearchChange(event: any) {
    this.isExactSearch = event.checked;
    // Realizar nueva búsqueda con el término actual
    this.loadDocuments(this.currentSearchTerm);
  }

  handleSearchResults(results: any) {
    const documents = results.results.map((result: any) => {
      return result.matching_pages.map((page: any) => ({
        _id: result.filename, // Utilizar el nombre del archivo como ID
        _source: {
          name_document: result.filename,
          content: Array.isArray(page.highlights) ? page.highlights.join(' ') : page.highlights, // Verificar si highlights es un array
          page_number: page.page_number, // Número de página
          total_pages: result.total_pages,
          relative_path: result.relative_path // Path relativo
        }
      }));
    }).flat(); // Aplanar el array de páginas
    this.dataSource.data = documents;
  }
    checkNewFiles(): void {
    this.isCheckingNewFiles = true;
    this.logger.info('Iniciando detección de archivos nuevos', {
      component: 'DocumentSearchComponent',
      action: 'checkNewFiles'
    });
    this.documentService.checkNewFiles().subscribe({
      next: (response) => {
        this.logger.success('Detección de archivos completada', {
          component: 'DocumentSearchComponent',
          action: 'checkNewFiles',
          details: {
            total_found: response.total_found,
            total_processed: response.total_processed
          }
        });
        // Abrir el modal con los resultados
        this.dialog.open(FileDetectionDialogComponent, {
          width: '500px',
          data: response
        });
        
        // Recargar los documentos después de detectar nuevos archivos
        this.loadDocuments(this.currentSearchTerm);
      },
      error: (error) => {
        this.logger.error('Error en la detección de archivos', {
          component: 'DocumentSearchComponent',
          action: 'checkNewFiles',
          details: error
        });
        // Mostrar error en el modal
        this.dialog.open(FileDetectionDialogComponent, {
          width: '500px',
          data: {
            status: 'error',
            total_found: 0,
            total_processed: 0,
            processed_files: [],
            failed_files: [{
              path: 'Error del sistema',
              error: error.message || 'Error desconocido al verificar archivos'
            }]
          }
        });
      },
      complete: () => {
        this.logger.info('Proceso de detección finalizado', {
          component: 'DocumentSearchComponent',
          action: 'checkNewFiles'
        });
        this.isCheckingNewFiles = false;
      }
    });
  }
  loadDocuments(searchTerm: string = ''): void {
    this.isLoading = true;
    this.logger.info('Cargando documentos', {
      component: 'DocumentSearchComponent',
      action: 'loadDocuments',
      details: { searchTerm }
    });
    // Elegir el método de búsqueda según el estado del checkbox
    const searchMethod = this.isExactSearch ? 
      this.documentService.exactSearchDocuments(searchTerm) :
      this.documentService.searchDocuments(searchTerm);

    // Suscribirse al método de búsqueda seleccionado
    searchMethod.subscribe({
      next: (response) => {
        // Mapear los resultados de la búsqueda a la estructura de DocumentData
        const documents = response.results.map((result: any) => {
          return result.matching_pages.map((page: any) => ({
            _id: result.filename, // Utilizar el nombre del archivo como ID
            _source: {
              name_document: result.filename,
              content: Array.isArray(page.content) ? page.content.join(' ') : page.content, // Verificar si highlights es un array
              page_number: page.page_number, // Número de página
              total_pages: result.total_pages,
              relative_path: result.relative_path // Path relativo
            }
          }));
        }).flat(); // Aplanar el array de páginas
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