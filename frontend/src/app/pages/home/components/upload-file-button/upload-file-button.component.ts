// file-upload.component.ts
import { Component, Input, ViewChild, ElementRef, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpClient } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { EventEmitter, Output } from '@angular/core';
import { DocumentService } from '../../services/documents-search.service';
import { environment } from '../../../../../environments/enviroment';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    FormsModule
  ],
  templateUrl: './upload-file-button.component.html',
  styleUrls: ['./upload-file-button.component.css']
})

export class FileUploadComponent {
  private http = inject(HttpClient);
  private snackBar = inject(MatSnackBar);
  private documentCountService = inject(DocumentService);
  private apiUrl = environment.apiUrl; // URL base

  @Input() accept = '.txt';
  @Input() chooseLabel = 'Buscar con archivo';
  @Input() deleteButtonLabel = 'Eliminar archivo';
  @Input() deleteButtonIcon = 'close';

  @ViewChild('fileUpload') fileUpload!: ElementRef<HTMLInputElement>;

  files = signal<File[]>([]);
  inputFileName = '';

  onClick(event: Event): void {
    this.fileUpload?.nativeElement.click();
  }

  onInput(event: Event): void {
    // Se mantiene para ngModel
  }

  onFileSelected(event: Event): void {
    const element = event.target as HTMLInputElement;
    const fileList: FileList | null = element.files;

    if (fileList) {
      const file = fileList[0];
      if (file.type === 'text/plain') {
        this.files.set([file]);
        this.readFileContent(file);
      } else {
        this.snackBar.open('Por favor selecciona un archivo .txt', 'Cerrar', {
          duration: 3000
        });
      }
    }
  }

  private readFileContent(file: File): void {
    const reader = new FileReader();
    
    reader.onload = (e: ProgressEvent<FileReader>) => {
      const content = e.target?.result as string;
      // Guardamos en localStorage
      localStorage.setItem('searchContent', content);
      // Realizamos la búsqueda
      this.searchWithContent(content);
    };

    reader.onerror = (error) => {
      console.error('Error al leer el archivo:', error);
      this.snackBar.open('Error al leer el archivo', 'Cerrar', {
        duration: 3000
      });
    };

    reader.readAsText(file);
  }

  private searchWithContent(content: string): void {
    // Hacemos la petición al endpoint normal de búsqueda
    this.http.get(`${this.apiUrl}/api_documents/search`, {
      params: {
        search_term: content,
        index_name: 'pdfs',
      }
    }).pipe(
      catchError(error => {
        console.error('Error en la búsqueda:', error);
        this.snackBar.open('Error al realizar la búsqueda', 'Cerrar', {
          duration: 3000
        });
        return throwError(() => error);
      })
    ).subscribe({
      next: (response: any) => {
        // Guardamos los resultados en localStorage también

        const count = response.results.length || 0;
        this.documentCountService.updateCount(count); // Actualizamos el contador
        localStorage.setItem('searchResults', JSON.stringify(response));
        this.snackBar.open('Búsqueda realizada con éxito', 'Cerrar', {
          duration: 3000
        });
      }
    });
  }

  removeFile(event: Event, fileToRemove: File): void {
    this.files.update(files =>
      files.filter(file => file !== fileToRemove)
    );
    event.stopPropagation();
    // Limpiamos también el localStorage
    localStorage.removeItem('searchContent');
    localStorage.removeItem('searchResults');
    this.clearInputElement();
  }

  private clearInputElement(): void {
    this.fileUpload.nativeElement.value = '';
    this.inputFileName = '';
  }
}