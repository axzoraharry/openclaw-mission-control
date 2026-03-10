// AxzoraApp.kt - Main Application Class
package com.axzora.superapp

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class AxzoraApp : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Initialize app components
    }
}
